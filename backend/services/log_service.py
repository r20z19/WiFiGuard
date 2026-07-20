from database import get_db
from utils.time_utils import now_str


def add_log(level="INFO", category="system", message="", detail=""):
    """Add a log entry to the system_logs table."""
    conn = get_db()
    conn.execute(
        """INSERT INTO system_logs (timestamp, level, category, message, detail)
           VALUES (?, ?, ?, ?, ?)""",
        (now_str(), level, category, message, detail),
    )
    conn.commit()
    conn.close()


def get_logs(level=None, category=None, search=None, limit=200):
    """Query logs with optional filters."""
    conn = get_db()
    query = "SELECT * FROM system_logs WHERE 1=1"
    params = []

    if level:
        query += " AND level = ?"
        params.append(level)
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (message LIKE ? OR detail LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_log_stats():
    """Return log counts by level."""
    conn = get_db()
    rows = conn.execute(
        "SELECT level, COUNT(*) as cnt FROM system_logs GROUP BY level"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM system_logs").fetchone()[0]
    conn.close()
    return {"total": total, "byLevel": {r["level"]: r["cnt"] for r in rows}}


def export_logs(level=None, category=None, search=None):
    """Export all matching logs as a list of dicts."""
    conn = get_db()
    query = "SELECT * FROM system_logs WHERE 1=1"
    params = []

    if level:
        query += " AND level = ?"
        params.append(level)
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (message LIKE ? OR detail LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY timestamp DESC LIMIT 10000"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row):
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "level": row["level"],
        "category": row["category"],
        "message": row["message"],
        "detail": row["detail"],
    }
