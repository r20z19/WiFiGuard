from database import get_db
from utils.time_utils import now_str


def get_all():
    conn = get_db()
    rows = conn.execute("SELECT * FROM blacklist ORDER BY added_at DESC").fetchall()
    conn.close()
    return [
        {
            "mac": r["mac"],
            "name": r["name"],
            "reason": r["reason"],
            "addedAt": r["added_at"],
        }
        for r in rows
    ]


def is_whitelisted(mac):
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM whitelist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None


def add(mac, name, reason):
    if is_whitelisted(mac):
        return False, "该设备已在白名单中，无法添加到黑名单"

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO blacklist (mac, name, reason, added_at) VALUES (?, ?, ?, ?)",
        (mac, name, reason, now_str()),
    )
    conn.commit()
    conn.close()
    return True, None


def remove(mac):
    conn = get_db()
    conn.execute("DELETE FROM blacklist WHERE mac = ?", (mac,))
    conn.commit()
    conn.close()


def is_blacklisted(mac):
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM blacklist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None
