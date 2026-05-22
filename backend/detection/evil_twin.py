from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_BEACON, FC_PROBE_RESP
from utils.time_utils import now_str


class EvilTwinDetector(BaseDetector):
    name = "钓鱼AP"
    severity = "critical"
    suggestion = (
        "发现疑似钓鱼AP（Evil Twin），同一SSID被多个不同的BSSID广播。"
        "请确认周围是否存在同名WiFi，建议立即断开当前连接并验证AP的BSSID是否为合法设备。"
        "使用802.11w PMF可提供额外保护。"
    )

    def __init__(self):
        self._ssid_bssids = defaultdict(set)
        self._alerted_ssids = set()

    def analyze(self, frames):
        for f in frames:
            ft = f["frameType"]
            if ft not in (FC_BEACON, FC_PROBE_RESP):
                continue
            ssid = f.get("ssid", "")
            bssid = f.get("bssid", "") or f.get("sa", "")
            if not ssid or not bssid:
                continue

            ssid_key = ssid.strip()
            self._ssid_bssids[ssid_key].add(bssid)

            if len(self._ssid_bssids[ssid_key]) >= 2 and ssid_key not in self._alerted_ssids:
                self._alerted_ssids.add(ssid_key)
                bssid_list = ", ".join(sorted(self._ssid_bssids[ssid_key]))
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": list(self._ssid_bssids[ssid_key])[1],
                    "targetMac": list(self._ssid_bssids[ssid_key])[0],
                    "timestamp": now_str(),
                    "suggestion": (
                        f"{self.suggestion} "
                        f"检测到SSID '{ssid_key}' 由多个BSSID广播: {bssid_list}"
                    ),
                }

        return None

    def reset(self):
        self._ssid_bssids.clear()
        self._alerted_ssids.clear()
