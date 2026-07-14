import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)


def _load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


def _detect_wireless_interface():
    try:
        result = subprocess.run(
            ["iw", "dev"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    interfaces = []
    current = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("Interface "):
            current = {"name": line.split()[1], "type": ""}
            interfaces.append(current)
        elif current and line.startswith("type "):
            current["type"] = line.split()[1]

    for interface in interfaces:
        if interface["type"] == "monitor":
            return interface["name"]
    return interfaces[0]["name"] if interfaces else None


_load_env_file(os.path.join(PROJECT_DIR, ".env"))
_load_env_file(os.path.join(BASE_DIR, ".env"))

DATABASE_PATH = os.environ.get("WIFIGUARD_DB", os.path.join(BASE_DIR, "data", "wifiguard.db"))

MONITOR_INTERFACE = os.environ.get("WIFIGUARD_IFACE") or _detect_wireless_interface() or "wlan1mon"

SIMULATION_MODE = os.environ.get("WIFIGUARD_SIM", "true").lower() == "true"

DETECTION_INTERVAL = int(os.environ.get("WIFIGUARD_INTERVAL", "2"))

LIVE_LOG_INTERVAL = int(os.environ.get("WIFIGUARD_LIVE_LOG_INTERVAL", "10"))

TARGET_SSID = os.environ.get("WIFIGUARD_NAME", "")
TARGET_BSSID = os.environ.get("WIFIGUARD_BSSID", "").lower()

# Access control modes:
#   monitor    only alert/log
#   blacklist  deauth clients listed in blacklist (uses WPA2 weakness)
#   whitelist  deauth clients not listed in whitelist (uses WPA2 weakness)
ACCESS_CONTROL_MODE = os.environ.get("WIFIGUARD_ACCESS_MODE", "monitor").lower()
DEAUTH_COUNT = int(os.environ.get("WIFIGUARD_DEAUTH_COUNT", "5"))
DEAUTH_COOLDOWN_SECONDS = int(os.environ.get("WIFIGUARD_DEAUTH_COOLDOWN", "30"))

PCAP_FILE_PATHS = os.environ.get("WIFIGUARD_PCAP", "")

EMAIL_SMTP_HOST = os.environ.get("WIFIGUARD_SMTP_HOST", "smtp.qq.com")
EMAIL_SMTP_PORT = int(os.environ.get("WIFIGUARD_SMTP_PORT", "465"))
EMAIL_SMTP_TIMEOUT = 10
