from detection.base import BaseDetector
from utils.time_utils import now_str


class WeakEncryptionDetector(BaseDetector):
    name = "弱加密协议"
    severity = "medium"
    suggestion = (
        "检测到网络使用不安全的加密协议（WEP/WPA/WPA2-TKIP），"
        "攻击者可利用已知漏洞破解WiFi密码或解密通信内容。"
        "建议将加密协议升级至WPA2-AES或WPA3-SAE，"
        "并确保禁用WEP和WPA-TKIP等过时协议。"
    )

    # Weak encryption protocols to detect
    WEAK_ENCRYPTIONS = ["WEP", "WPA", "WPA2-TKIP", "TKIP"]

    def __init__(self):
        self._beacon_checked = False

    def analyze(self, frames):
        if self._beacon_checked:
            return None

        for f in frames:
            info = f.get("info", "")

            # Check for WEP/WPA1/TKIP in beacon/probe response info
            for enc in self.WEAK_ENCRYPTIONS:
                if enc in info:
                    self._beacon_checked = True
                    return {
                        "type": self.name,
                        "severity": self.severity,
                        "sourceMac": f.get("sa", "N/A"),
                        "targetMac": "N/A",
                        "timestamp": now_str(),
                        "suggestion": self.suggestion,
                    }

        return None

    def reset(self):
        self._beacon_checked = False
