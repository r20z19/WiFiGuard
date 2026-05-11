from database import get_db
from utils.time_utils import now_str


def get_online_devices():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM devices_online ORDER BY last_seen DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def upsert_device(device):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM devices_online WHERE mac = ?", (device["mac"],)
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE devices_online
               SET ip = ?, ssid = ?, signal = ?, status = ?, last_seen = ?
               WHERE mac = ?""",
            (
                device.get("ip", existing["ip"]),
                device.get("ssid", existing["ssid"]),
                device.get("signal", existing["signal"]),
                device.get("status", existing["status"]),
                device.get("last_seen", now_str()),
                device["mac"],
            ),
        )
    else:
        conn.execute(
            """INSERT INTO devices_online (mac, ip, ssid, signal, status, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                device["mac"],
                device.get("ip", ""),
                device.get("ssid", ""),
                device.get("signal", -70),
                device.get("status", "正常"),
                device.get("first_seen", now_str()),
                device.get("last_seen", now_str()),
            ),
        )

    conn.commit()
    conn.close()


def bulk_upsert(devices):
    for d in devices:
        upsert_device(d)


def remove_stale_devices(threshold_seconds=120):
    conn = get_db()
    conn.execute(
        """DELETE FROM devices_online
           WHERE datetime(last_seen) < datetime('now', ? || ' seconds', 'localtime')""",
        (f"-{threshold_seconds}",),
    )
    conn.commit()
    conn.close()


def _row_to_dict(row):
    return {
        "mac": row["mac"],
        "ip": row["ip"],
        "ssid": row["ssid"],
        "signal": row["signal"],
        "status": row["status"],
        "firstSeen": row["first_seen"],
        "lastSeen": row["last_seen"],
    }
