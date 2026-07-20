from database import get_db
from utils.time_utils import now_str
from utils.mac_utils import normalize_mac
from services.log_service import add_log


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
    mac = normalize_mac(mac)
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM whitelist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None


def add(mac, name, reason):
    mac = normalize_mac(mac)
    if is_whitelisted(mac):
        return False, "该设备已在白名单中，无法添加到黑名单"

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO blacklist (mac, name, reason, added_at) VALUES (?, ?, ?, ?)",
        (mac, name, reason, now_str()),
    )
    conn.commit()
    conn.close()
    add_log("WARNING", "config", f"设备加入黑名单: {mac}", f"名称={name} 原因={reason}")
    return True, None


def remove(mac):
    mac = normalize_mac(mac)
    conn = get_db()
    conn.execute("DELETE FROM blacklist WHERE mac = ?", (mac,))
    conn.commit()
    conn.close()
    add_log("INFO", "config", f"设备移出黑名单: {mac}")


def is_blacklisted(mac):
    mac = normalize_mac(mac)
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM blacklist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None


def get_mac_set():
    conn = get_db()
    rows = conn.execute("SELECT mac FROM blacklist").fetchall()
    conn.close()
    return {r["mac"].lower() for r in rows}
