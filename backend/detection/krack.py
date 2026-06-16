from detection.base import BaseDetector
from utils.time_utils import now_str


class KrackDetector(BaseDetector):
    name = "KRACK风险"
    severity = "critical"
    suggestion = (
        "检测到网络使用存在KRACK（Key Reinstallation Attack）漏洞的加密协议。"
        "WPA2-TKIP和WPA1易受密钥重装攻击。建议立即升级AP固件至最新版本，"
        "并将加密方式切换为WPA2-AES（CCMP）或WPA3。"
        "同时确保所有客户端设备已安装最新的安全补丁。"
    )

    # Vulnerable cipher suites
    CIPHER_TKIP = "TKIP"
    CIPHER_WEP = "WEP"

    def __init__(self):
        self._checked = False

    def analyze(self, frames):
        if self._checked:
            return None

        for f in frames:
            info = f.get("info", "")

            # Check info field for vulnerable encryption indicators
            upper_info = info.upper()
            if self.CIPHER_TKIP in upper_info:
                self._checked = True
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": f.get("sa", "N/A"),
                    "targetMac": "N/A",
                    "timestamp": now_str(),
                    "suggestion": (
                        "检测到网络使用TKIP加密，存在KRACK漏洞风险。"
                        + self.suggestion
                    ),
                }

            if self.CIPHER_WEP in upper_info:
                self._checked = True
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": f.get("sa", "N/A"),
                    "targetMac": "N/A",
                    "timestamp": now_str(),
                    "suggestion": (
                        "检测到网络使用WEP加密，WEP已被完全破解且易受多种攻击。"
                        + self.suggestion
                    ),
                }

            # Check for WPA version 1
            if "WPA Version" in info or "WPA version" in info:
                self._checked = True
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": f.get("sa", "N/A"),
                    "targetMac": "N/A",
                    "timestamp": now_str(),
                    "suggestion": (
                        "检测到网络使用WPA1，存在已知安全漏洞。"
                        + self.suggestion
                    ),
                }

        return None

    def reset(self):
        self._checked = False
