from database import get_db
from utils.time_utils import now_str


def get_all():
    conn = get_db()
    rows = conn.execute("SELECT * FROM whitelist ORDER BY added_at DESC").fetchall()
    conn.close()
    return [
        {"mac": r["mac"], "name": r["name"], "addedAt": r["added_at"]} for r in rows
    ]


def add(mac, name):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO whitelist (mac, name, added_at) VALUES (?, ?, ?)",
        (mac, name, now_str()),
    )
    conn.commit()
    conn.close()


def remove(mac):
    conn = get_db()
    conn.execute("DELETE FROM whitelist WHERE mac = ?", (mac,))
    conn.commit()
    conn.close()


def is_whitelisted(mac):
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM whitelist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None
