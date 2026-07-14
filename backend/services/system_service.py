import time

from config import ACCESS_CONTROL_MODE, MONITOR_INTERFACE, SIMULATION_MODE, TARGET_BSSID, TARGET_SSID

_start_time = time.time()


def get_status():
    return {
        "status": "listening",
        "uptime": int(time.time() - _start_time),
        "monitorInterface": MONITOR_INTERFACE if not SIMULATION_MODE else "simulation",
        "targetSsid": TARGET_SSID,
        "targetBssid": TARGET_BSSID,
        "accessControlMode": ACCESS_CONTROL_MODE,
    }
