import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.environ.get("WIFIGUARD_DB", os.path.join(BASE_DIR, "data", "wifiguard.db"))

MONITOR_INTERFACE = os.environ.get("WIFIGUARD_IFACE", "wlan1mon")

SIMULATION_MODE = os.environ.get("WIFIGUARD_SIM", "true").lower() == "true"

DETECTION_INTERVAL = int(os.environ.get("WIFIGUARD_INTERVAL", "2"))

EMAIL_SMTP_HOST = os.environ.get("WIFIGUARD_SMTP_HOST", "smtp.qq.com")
EMAIL_SMTP_PORT = int(os.environ.get("WIFIGUARD_SMTP_PORT", "465"))
EMAIL_SMTP_TIMEOUT = 10
