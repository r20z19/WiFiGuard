from database import get_db
from utils.time_utils import now_str
from utils.mac_utils import normalize_mac
from services.log_service import add_log


def get_all():
    conn = get_db()
    rows = conn.execute("SELECT * FROM whitelist ORDER BY added_at DESC").fetchall()
    conn.close()
    return [
        {
            "mac": r["mac"],
            "name": r["name"],
            "deviceType": r["device_type"] or "",
            "addedAt": r["added_at"],
        }
        for r in rows
    ]


def is_blacklisted(mac):
    mac = normalize_mac(mac)
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM blacklist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None


def add(mac, name, device_type=""):
    mac = normalize_mac(mac)
    if is_blacklisted(mac):
        return False, "该设备已在黑名单中，无法添加到白名单"

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO whitelist (mac, name, added_at, device_type) VALUES (?, ?, ?, ?)",
        (mac, name, now_str(), device_type),
    )
    conn.commit()
    conn.close()
    add_log("INFO", "config", f"设备加入白名单: {mac}", f"名称={name} 类型={device_type}")

    # Sync to nftables: allow this MAC to forward traffic
    try:
        from services.nftables_service import add_trusted
        add_trusted(mac)
    except Exception as e:
        print(f"[whitelist] nftables sync failed: {e}")

    return True, None


def remove(mac):
    mac = normalize_mac(mac)
    conn = get_db()
    conn.execute("DELETE FROM whitelist WHERE mac = ?", (mac,))
    conn.commit()
    conn.close()
    add_log("INFO", "config", f"设备移出白名单: {mac}")

    # Sync to nftables: revoke forwarding permission
    try:
        from services.nftables_service import remove_trusted
        remove_trusted(mac)
    except Exception as e:
        print(f"[whitelist] nftables sync failed: {e}")


def is_whitelisted(mac):
    mac = normalize_mac(mac)
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM whitelist WHERE mac = ?", (mac,)
    ).fetchone()
    conn.close()
    return row is not None


def get_mac_set():
    conn = get_db()
    rows = conn.execute("SELECT mac FROM whitelist").fetchall()
    conn.close()
    return {r["mac"].lower() for r in rows}
