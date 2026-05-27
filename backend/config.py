import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.environ.get("WIFIGUARD_DB", os.path.join(BASE_DIR, "data", "wifiguard.db"))

# Wireless interface for live monitor-mode capture.
# Run scripts/setup_monitor.sh to put the interface into monitor mode first.
# Common names: wlan1 (USB adapter), wlan1mon (airmon-ng renamed), wlp0s20f0u1 (systemd)
MONITOR_INTERFACE = os.environ.get("WIFIGUARD_IFACE", "wlan1mon")

# Set WIFIGUARD_SIM=false to use live capture mode (requires MONITOR_INTERFACE)
SIMULATION_MODE = os.environ.get("WIFIGUARD_SIM", "true").lower() == "true"

DETECTION_INTERVAL = int(os.environ.get("WIFIGUARD_INTERVAL", "2"))

# Pcap replay mode: when SIMULATION_MODE=false and these are set, read from pcap files
# Comma-separated list of pcap file paths
PCAP_FILE_PATHS = os.environ.get("WIFIGUARD_PCAP", "")

EMAIL_SMTP_HOST = os.environ.get("WIFIGUARD_SMTP_HOST", "smtp.qq.com")
EMAIL_SMTP_PORT = int(os.environ.get("WIFIGUARD_SMTP_PORT", "465"))
EMAIL_SMTP_TIMEOUT = 10
