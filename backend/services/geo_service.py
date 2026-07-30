import json
import urllib.request
import urllib.error
from database import get_db


# Cache for IP geolocation results
_geo_cache = {}


def geolocate_ip(ip):
    """Resolve an IP address to geographic coordinates.
    Uses ip-api.com free API (no key required, 45 requests/minute limit).
    Returns dict with lat, lng, city, country, or None on failure.
    """
    if not ip or ip in ("0.0.0.0", "127.0.0.1", "::1", "localhost"):
        return None
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
        # Private IPs - return None so frontend can use a default location
        return None
    if ip in _geo_cache:
        return _geo_cache[ip]

    try:
        url = f"http://ip-api.com/json/{ip}?fields=lat,lon,city,country"
        req = urllib.request.Request(url, headers={"User-Agent": "WiFiGuard/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("lat") is not None and data.get("lon") is not None:
                result = {
                    "lat": data["lat"],
                    "lng": data["lon"],
                    "city": data.get("city", ""),
                    "country": data.get("country", ""),
                }
                _geo_cache[ip] = result
                return result
    except Exception:
        pass
    return None


def get_network_locations():
    """Return all online devices and alerts for network map visualization."""
    from services.device_service import get_online_devices

    conn = get_db()
    alerts = conn.execute(
        "SELECT id, type, severity, source_mac, target_mac, timestamp, suggestion, status "
        "FROM alerts_current ORDER BY timestamp DESC"
    ).fetchall()
    whitelist_macs = {
        r["mac"].lower(): {"name": r["name"], "device_type": r["device_type"] or ""}
        for r in conn.execute("SELECT mac, name, device_type FROM whitelist").fetchall()
    }
    blacklist_macs = {r["mac"].lower() for r in conn.execute("SELECT mac FROM blacklist").fetchall()}
    conn.close()

    # AP BSSID
    ap_mac = None
    try:
        from services.hostapd_service import get_status
        status = get_status()
        if status:
            ap_mac = (status.get("bssid[0]") or status.get("bssid") or "").lower()
    except Exception:
        pass

    # Build device list from hostapd (live data)
    devices = get_online_devices()
    device_list = []
    known_macs = set()
    for d in devices:
        mac = d["mac"].lower()
        known_macs.add(mac)
        device_type = "client"
        name = ""
        dev_class = ""
        if mac == ap_mac:
            device_type = "ap"
            name = "AP"
        elif mac in blacklist_macs:
            device_type = "blacklisted"
        elif mac in whitelist_macs:
            device_type = "whitelisted"
            name = whitelist_macs[mac]["name"]
            dev_class = whitelist_macs[mac]["device_type"]

        device_list.append({
            "mac": d["mac"],
            "name": name,
            "deviceType": dev_class,
            "ip": d.get("ip", ""),
            "ssid": d.get("ssid", ""),
            "signal": d.get("signal", -70),
            "status": d.get("status", "正常"),
            "vendor": d.get("vendor", ""),
            "type": device_type,
        })

    # Build alert list — only include recent alerts (2 min) for topology rendering
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(minutes=2)

    alert_list = []
    for a in alerts:
        # Filter: only recent alerts appear on the live topology
        try:
            alert_time = datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S")
            if alert_time < cutoff:
                continue
        except (ValueError, TypeError):
            pass
        alert_list.append({
            "id": a["id"],
            "type": a["type"],
            "severity": a["severity"],
            "sourceMac": a["source_mac"] or "",
            "targetMac": a["target_mac"] or "",
            "timestamp": a["timestamp"],
            "suggestion": a["suggestion"] or "",
            "status": a["status"] or "未处理",
        })

    # Inject attackers from recent alerts into device list
    # so the topology can render them; they disappear after the time window
    UNKNOWN_ATTACKER_MAC = "ff:ff:ff:00:00:01"
    # Only these alert types represent actual external attacks
    ATTACK_TYPES = {"Deauth攻击", "暴力破解", "Flood泛洪", "钓鱼AP", "非法接入"}
    known_macs_set = set(known_macs)
    has_unknown_attacker = False
    for a in alert_list:
        if a["type"] not in ATTACK_TYPES:
            continue
        src = (a["sourceMac"] or "").lower()
        if not src:
            continue
        # Sentinel MAC or AP's own MAC → virtual unknown attacker node
        if src == UNKNOWN_ATTACKER_MAC or src == ap_mac:
            if not has_unknown_attacker:
                has_unknown_attacker = True
                known_macs_set.add(UNKNOWN_ATTACKER_MAC)
                device_list.append({
                    "mac": UNKNOWN_ATTACKER_MAC,
                    "ip": "",
                    "ssid": "",
                    "signal": -90,
                    "status": "可疑",
                    "vendor": "未知攻击者",
                    "type": "blacklisted",
                })
            a["sourceMac"] = UNKNOWN_ATTACKER_MAC
        elif src not in known_macs_set:
            known_macs_set.add(src)
            device_list.append({
                "mac": src,
                "ip": "",
                "ssid": "",
                "signal": -80,
                "status": "可疑",
                "vendor": "",
                "type": "blacklisted",
            })

    return {"devices": device_list, "alerts": [a for a in alert_list if a["type"] in ATTACK_TYPES]}
