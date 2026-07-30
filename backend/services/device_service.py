from database import get_db
from utils.time_utils import now_str
from utils.oui_db import lookup_vendor


def get_online_devices():
    """获取在线设备列表: AP 自身 + hostapd 关联的站点"""
    from services.hostapd_service import get_connected_stations, get_status

    devices = []
    now = now_str()

    # AP 自身
    try:
        status = get_status()
        if status:
            ap_mac = (status.get("bssid[0]") or status.get("bssid") or "").lower()
            ap_ssid = status.get("ssid[0]") or status.get("ssid") or ""
            if ap_mac:
                devices.append({
                    "mac": ap_mac,
                    "ip": "",
                    "ssid": ap_ssid,
                    "signal": 0,
                    "status": "正常",
                    "firstSeen": "",
                    "lastSeen": now,
                    "vendor": "",
                    "pairwiseCipher": "",
                    "groupCipher": "",
                    "akm": "",
                })
    except Exception:
        pass

    # 关联的客户端
    try:
        stations = get_connected_stations()
        for sta in stations:
            mac = sta.get("mac", "").lower()
            if not mac:
                continue
            signal = int(sta.get("signal", -50)) or -50
            devices.append({
                "mac": mac,
                "ip": "",
                "ssid": devices[0]["ssid"] if devices else "",
                "signal": signal,
                "status": "正常",
                "firstSeen": "",
                "lastSeen": now,
                "vendor": lookup_vendor(mac),
                "pairwiseCipher": "",
                "groupCipher": "",
                "akm": "",
            })
    except Exception:
        pass

    # 补充数据库中的额外信息 (ip, vendor, firstSeen 等)
    conn = get_db()
    for dev in devices:
        row = conn.execute(
            "SELECT * FROM devices_online WHERE mac = ?", (dev["mac"],)
        ).fetchone()
        if row:
            dev["ip"] = row["ip"] or dev["ip"]
            dev["vendor"] = row["vendor"] or dev["vendor"]
            dev["firstSeen"] = row["first_seen"] or dev["firstSeen"]
            dev["pairwiseCipher"] = row["pairwise_cipher"] or dev["pairwiseCipher"]
            dev["groupCipher"] = row["group_cipher"] or dev["groupCipher"]
            dev["akm"] = row["akm"] or dev["akm"]
    conn.close()

    return devices


def upsert_device(device):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM devices_online WHERE mac = ?", (device["mac"],)
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE devices_online
               SET ip = ?, ssid = ?, signal = ?, status = ?, last_seen = ?,
                   vendor = ?, pairwise_cipher = ?, group_cipher = ?, akm = ?
               WHERE mac = ?""",
            (
                device.get("ip", existing["ip"]),
                device.get("ssid", existing["ssid"]),
                device.get("signal", existing["signal"]),
                device.get("status", existing["status"]),
                device.get("last_seen", now_str()),
                device.get("vendor", existing["vendor"]),
                device.get("pairwiseCipher", existing["pairwise_cipher"]),
                device.get("groupCipher", existing["group_cipher"]),
                device.get("akm", existing["akm"]),
                device["mac"],
            ),
        )
    else:
        conn.execute(
            """INSERT INTO devices_online
               (mac, ip, ssid, signal, status, first_seen, last_seen,
                vendor, pairwise_cipher, group_cipher, akm)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                device["mac"],
                device.get("ip", ""),
                device.get("ssid", ""),
                device.get("signal", -70),
                device.get("status", "正常"),
                device.get("first_seen", now_str()),
                device.get("last_seen", now_str()),
                device.get("vendor", ""),
                device.get("pairwiseCipher", ""),
                device.get("groupCipher", ""),
                device.get("akm", ""),
            ),
        )

    conn.commit()
    conn.close()


def bulk_upsert(devices):
    if not devices:
        return

    conn = get_db()
    try:
        for device in devices:
            existing = conn.execute(
                "SELECT * FROM devices_online WHERE mac = ?", (device["mac"],)
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE devices_online
                       SET ip = ?, ssid = ?, signal = ?, status = ?, last_seen = ?,
                           vendor = ?, pairwise_cipher = ?, group_cipher = ?, akm = ?
                       WHERE mac = ?""",
                    (
                        device.get("ip") or existing["ip"],
                        device.get("ssid") or existing["ssid"],
                        device.get("signal", existing["signal"]),
                        device.get("status") or existing["status"],
                        device.get("last_seen", now_str()),
                        device.get("vendor") or existing["vendor"],
                        device.get("pairwiseCipher") or existing["pairwise_cipher"],
                        device.get("groupCipher") or existing["group_cipher"],
                        device.get("akm") or existing["akm"],
                        device["mac"],
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO devices_online
                       (mac, ip, ssid, signal, status, first_seen, last_seen,
                        vendor, pairwise_cipher, group_cipher, akm)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        device["mac"],
                        device.get("ip", ""),
                        device.get("ssid", ""),
                        device.get("signal", -70),
                        device.get("status", "正常"),
                        device.get("first_seen", now_str()),
                        device.get("last_seen", now_str()),
                        device.get("vendor", ""),
                        device.get("pairwiseCipher", ""),
                        device.get("groupCipher", ""),
                        device.get("akm", ""),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


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
        "vendor": row["vendor"],
        "pairwiseCipher": row["pairwise_cipher"],
        "groupCipher": row["group_cipher"],
        "akm": row["akm"],
    }
