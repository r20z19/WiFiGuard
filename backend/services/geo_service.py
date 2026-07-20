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
    """Return all online devices with geolocation data, plus alerts for attack visualization."""
    conn = get_db()

    devices = conn.execute(
        "SELECT mac, ip, ssid, signal, status, vendor, last_seen "
        "FROM devices_online ORDER BY last_seen DESC"
    ).fetchall()

    alerts = conn.execute(
        "SELECT id, type, severity, source_mac, target_mac, timestamp, suggestion, status "
        "FROM alerts_current ORDER BY timestamp DESC"
    ).fetchall()

    whitelist_rows = conn.execute("SELECT mac FROM whitelist").fetchall()
    blacklist_rows = conn.execute("SELECT mac FROM blacklist").fetchall()

    conn.close()

    whitelist_macs = {r["mac"] for r in whitelist_rows}
    blacklist_macs = {r["mac"] for r in blacklist_rows}

    # Build device list with geolocation
    device_list = []
    default_locations = [
        (39.9042, 116.4074, "Beijing"),    # China
        (31.2304, 121.4737, "Shanghai"),   # China
        (22.5431, 114.0579, "Shenzhen"),   # China
        (35.6762, 139.6503, "Tokyo"),      # Japan
        (37.7749, -122.4194, "SF"),        # USA
        (51.5074, -0.1278, "London"),      # UK
    ]

    for i, d in enumerate(devices):
        ip = d["ip"] if d["ip"] else ""
        geo = geolocate_ip(ip) if ip else None

        if geo is None:
            # Use a default location spread around for visualization
            default = default_locations[i % len(default_locations)]
            # Add slight random offset to spread devices
            import random
            random.seed(hash(d["mac"]) % (2**31))
            geo = {
                "lat": default[0] + random.uniform(-0.5, 0.5),
                "lng": default[1] + random.uniform(-0.5, 0.5),
                "city": default[2],
                "country": "",
            }

        device_type = "client"
        if d["mac"] in blacklist_macs:
            device_type = "blacklisted"
        if d["mac"] in whitelist_macs:
            device_type = "whitelisted"
        # Check if this device looks like an AP (has SSID and normal status)
        device_ssid = d["ssid"] if d["ssid"] else ""
        device_status = d["status"] if d["status"] else ""
        device_vendor = d["vendor"] if d["vendor"] else ""
        if device_ssid and device_status == "正常":
            # Devices with SSID that look like APs
            if device_vendor and any(
                kw in device_vendor.lower()
                for kw in ["cisco", "aruba", "ubiquiti", "tp-link", "huawei", "router", "network"]
            ):
                device_type = "ap"

        device_list.append({
            "mac": d["mac"],
            "ip": ip,
            "ssid": device_ssid,
            "signal": d["signal"] if d["signal"] else -70,
            "status": device_status if device_status else "正常",
            "vendor": device_vendor,
            "lat": geo["lat"],
            "lng": geo["lng"],
            "city": geo.get("city", ""),
            "country": geo.get("country", ""),
            "type": device_type,
        })

    # Build alert list with geolocation for source and target
    alert_list = []
    for a in alerts:
        src_mac = a["source_mac"]
        tgt_mac = a["target_mac"]

        src_device = next((d for d in device_list if d["mac"] == src_mac), None)
        tgt_device = next((d for d in device_list if d["mac"] == tgt_mac), None)

        alert_list.append({
            "id": a["id"],
            "type": a["type"],
            "severity": a["severity"],
            "sourceMac": src_mac if src_mac else "",
            "targetMac": tgt_mac if tgt_mac else "",
            "timestamp": a["timestamp"],
            "suggestion": a["suggestion"] if a["suggestion"] else "",
            "status": a["status"] if a["status"] else "未处理",
            "sourceLocation": {
                "lat": src_device["lat"] if src_device else 39.9,
                "lng": src_device["lng"] if src_device else 116.4,
            } if src_device else None,
            "targetLocation": {
                "lat": tgt_device["lat"] if tgt_device else 39.9,
                "lng": tgt_device["lng"] if tgt_device else 116.4,
            } if tgt_device else None,
        })

    return {
        "devices": device_list,
        "alerts": alert_list,
    }
