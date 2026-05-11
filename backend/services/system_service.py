import time

from config import MONITOR_INTERFACE, SIMULATION_MODE

_start_time = time.time()


def get_status():
    return {
        "status": "listening",
        "uptime": int(time.time() - _start_time),
        "monitorInterface": MONITOR_INTERFACE if not SIMULATION_MODE else "simulation",
    }
