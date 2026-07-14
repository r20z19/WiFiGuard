from detection.base import BaseDetector
from detection.packet_reader import FC_BEACON, FC_PROBE_RESP
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

    # Vulnerable cipher suite type codes from wlan.rsn.*.type
    TKIP_TYPE = "2"
    WEP40_TYPE = "1"
    WEP104_TYPE = "5"
    WEAK_TYPES = {"1": "WEP", "2": "TKIP", "5": "WEP"}

    def __init__(self):
        self._checked = False

    def analyze(self, frames):
        if self._checked:
            return None

        for f in frames:
            if f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                continue

            pairwise = str(f.get("pairwiseCipher", ""))
            group = str(f.get("groupCipher", ""))
            info = f.get("info", "")
            bssid = f.get("bssid", "") or f.get("sa", "N/A")
            ssid = f.get("ssid", "")

            # Check numeric cipher type fields (more reliable than info string)
            for field_name, value in [("成对加密", pairwise), ("组播加密", group)]:
                if value in self.WEAK_TYPES:
                    weak_name = self.WEAK_TYPES[value]
                    self._checked = True
                    return {
                        "type": self.name,
                        "severity": self.severity,
                        "sourceMac": bssid,
                        "targetMac": "N/A",
                        "timestamp": now_str(),
                        "suggestion": (
                            "SSID '{}' {}使用{}，该协议存在KRACK漏洞风险。{}"
                        ).format(ssid or "隐藏SSID", field_name, weak_name, self.suggestion),
                    }

            # WPA1 detection (vendor IE with "WPA" tag but without RSN)
            upper_info = info.upper()
            if ("WPA" in upper_info) and "RSN" not in info and "TKIP" in upper_info:
                self._checked = True
                return {
                    "type": self.name,
                    "severity": "critical",
                    "sourceMac": bssid,
                    "targetMac": "N/A",
                    "timestamp": now_str(),
                    "suggestion": (
                        "SSID '{}' 使用WPA1-TKIP，存在KRACK和其他已知安全漏洞。"
                    ).format(ssid or "隐藏SSID") + self.suggestion,
                }

        return None

    def reset(self):
        self._checked = False
