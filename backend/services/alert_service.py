from database import get_db
from utils.time_utils import now_str


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
    cursor = conn.execute(
        """INSERT INTO alerts_current (type, severity, source_mac, target_mac, timestamp, suggestion, status)
           VALUES (?, ?, ?, ?, ?, ?, '未处理')""",
        (
            alert_data["type"],
            alert_data["severity"],
            alert_data.get("sourceMac", alert_data.get("source_mac", "")),
            alert_data.get("targetMac", alert_data.get("target_mac", "")),
            alert_data.get("timestamp", now_str()),
            alert_data.get("suggestion", ""),
        ),
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
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

    conn.execute(
        """INSERT INTO alerts_history (id, type, severity, source_mac, target_mac, timestamp, suggestion, status, cleared_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, '已处理', ?)""",
        (
            alert["id"],
            alert["type"],
            alert["severity"],
            alert["sourceMac"],
            alert["targetMac"],
            alert["timestamp"],
            alert["suggestion"],
            now_str(),
        ),
    )
    conn.execute("DELETE FROM alerts_current WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
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
