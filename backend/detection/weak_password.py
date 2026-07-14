from detection.base import BaseDetector
from utils.time_utils import now_str


class WeakPasswordDetector(BaseDetector):
    name = "弱口令"
    severity = "low"
    suggestion = (
        "当前WiFi密码强度可能存在风险。攻击者可捕获WPA握手包后进行离线字典攻击。"
        "建议使用包含大小写字母、数字和特殊字符的至少12位密码，并避免使用默认SSID和默认密码。"
    )

    # Common weak/default SSID patterns that suggest default configuration
    WEAK_SSID_PATTERNS = [
        "TP-LINK", "TP-Link", "tplink", "TPLink",
        "D-Link", "dlink", "DLINK",
        "NETGEAR", "netgear",
        "ASUS", "asus",
        "Xiaomi", "xiaomi",
        "HUAWEI", "huawei", "Huawei",
        "CMCC", "ChinaNet", "ChinaUnicom",
        "admin", "default", "linksys", "Linksys",
    ]

    def __init__(self):
        self._beacon_checked = False

    def analyze(self, frames):
        if self._beacon_checked:
            return None

        for f in frames:
            ssid = f.get("ssid", "")
            if ssid:
                for pattern in self.WEAK_SSID_PATTERNS:
                    if pattern.lower() in ssid.lower():
                        self._beacon_checked = True
                        return {
                            "type": self.name,
                            "severity": self.severity,
                            "sourceMac": f.get("sa", "N/A"),
                            "targetMac": "N/A",
                            "timestamp": now_str(),
                            "suggestion": (
                                f"检测到疑似默认SSID '{ssid}'，可能存在弱口令风险。"
                                + self.suggestion
                            ),
                        }

        return None

    def reset(self):
        self._beacon_checked = False
