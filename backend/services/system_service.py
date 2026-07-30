import time

import config
from config import MONITOR_INTERFACE, SIMULATION_MODE, TARGET_BSSID, TARGET_SSID

_start_time = time.time()


def get_status():
    # Check hostapd status
    ap_status = None
    try:
        from services.hostapd_service import get_status as get_ap_status
        ap_status = get_ap_status()
    except Exception:
        pass

    return {
        "status": "listening",
        "uptime": int(time.time() - _start_time),
        "monitorInterface": MONITOR_INTERFACE if not SIMULATION_MODE else "simulation",
        "targetSsid": TARGET_SSID,
        "targetBssid": TARGET_BSSID,
        "whitelistEnabled": config.WHITELIST_ENABLED,
        "blacklistEnabled": config.BLACKLIST_ENABLED,
        "apEnabled": ap_status is not None,
        "apSsid": ap_status.get("ssid[0]", "WIFIGuard-Lab") if ap_status else None,
        "apChannel": ap_status.get("channel", None) if ap_status else None,
        "mode": "gateway",
    }
