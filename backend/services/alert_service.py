from database import get_db
from utils.time_utils import now_str
from services.log_service import add_log
from services.frame_service import log_attack_event


def get_current_alerts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM alerts_current ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_history_alerts(alert_type=None, status=None, start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT * FROM alerts_history WHERE 1=1"
    params = []

    if alert_type:
        query += " AND type = ?"
        params.append(alert_type)

    if status:
        query += " AND status = ?"
        params.append(status)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    query += " ORDER BY timestamp DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def create_alert(alert_data):
    conn = get_db()
    ts = alert_data.get("timestamp", now_str())
    source_mac = alert_data.get("sourceMac", alert_data.get("source_mac", ""))
    target_mac = alert_data.get("targetMac", alert_data.get("target_mac", ""))
    suggestion = alert_data.get("suggestion", "")

    cursor = conn.execute(
        """INSERT INTO alerts_current (type, severity, source_mac, target_mac, timestamp, suggestion, status)
           VALUES (?, ?, ?, ?, ?, ?, '未处理')""",
        (
            alert_data["type"],
            alert_data["severity"],
            source_mac,
            target_mac,
            ts,
            suggestion,
        ),
    )
    alert_id = cursor.lastrowid

    # Also write to history for permanent record
    conn.execute(
        """INSERT INTO alerts_history (id, type, severity, source_mac, target_mac, timestamp, suggestion, status, cleared_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, '未处理', NULL)""",
        (
            alert_id,
            alert_data["type"],
            alert_data["severity"],
            source_mac,
            target_mac,
            ts,
            suggestion,
        ),
    )
    conn.commit()
    conn.close()
    # Log to event buffer for AI analysis
    log_attack_event(
        alert_data["type"],
        alert_data.get("sourceMac", alert_data.get("source_mac", "")),
        alert_data.get("targetMac", alert_data.get("target_mac", "")),
        alert_data.get("severity", "medium"),
    )
    # Log the attack detection
    severity = alert_data.get("severity", "medium")
    log_level = "ERROR" if severity in ("critical", "high") else "WARNING"
    add_log(
        level=log_level,
        category="attack",
        message=f"检测到攻击: {alert_data['type']}",
        detail=f"源MAC={alert_data.get('sourceMac', alert_data.get('source_mac', ''))} "
               f"目标MAC={alert_data.get('targetMac', alert_data.get('target_mac', ''))} "
               f"严重等级={severity}",
    )
    return alert_id


def clear_alert(alert_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM alerts_current WHERE id = ?", (alert_id,)
    ).fetchone()

    if not row:
        conn.close()
        return False

    alert = _row_to_dict(row)

    # Update history record status to cleared
    conn.execute(
        """UPDATE alerts_history SET status = '已处理', cleared_at = ? WHERE id = ?""",
        (now_str(), alert_id),
    )
    conn.execute("DELETE FROM alerts_current WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    add_log("INFO", "attack", f"告警已处理: #{alert_id}", f"类型={alert.get('type','')} 源={alert.get('sourceMac','')}")
    return True


def _row_to_dict(row):
    return {
        "id": row["id"],
        "type": row["type"],
        "severity": row["severity"],
        "sourceMac": row["source_mac"],
        "targetMac": row["target_mac"],
        "timestamp": row["timestamp"],
        "suggestion": row["suggestion"],
        "status": row["status"],
    }
