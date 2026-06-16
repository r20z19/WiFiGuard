import time
from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_AUTH, FC_ASSOC_REQ, FC_ASSOC_RESP, FC_PROBE_REQ
from utils.time_utils import now_str


class IllegalAccessDetector(BaseDetector):
    name = "非法接入"
    severity = "high"
    suggestion = (
        "检测到未知设备尝试接入网络，该设备不在已知设备列表中。"
        "请确认该设备是否为合法设备。如非预期设备，建议立即将其加入黑名单，"
        "检查路由器DHCP租约记录，并考虑更换WiFi密码以防止未授权访问。"
    )

    def __init__(self, known_macs=None):
        self._known_macs = known_macs or set()
        self._ap_macs = set()
        self._seen_macs = defaultdict(list)
        self._alerted_macs = set()

    def set_known_macs(self, macs):
        self._known_macs = set(macs)

    def set_ap_macs(self, macs):
        self._ap_macs = set(macs)

    def add_known_mac(self, mac):
        self._known_macs.add(mac)

    def analyze(self, frames):
        for f in frames:
            ft = f["frameType"]
            if ft not in (FC_AUTH, FC_ASSOC_REQ):
                continue
            sa = f.get("sa", "")
            da = f.get("da", "")

            # Skip frames from known devices and APs
            if not sa or sa in self._known_macs or sa in self._ap_macs:
                continue

            # Track all unknown MACs that attempt auth/assoc
            if sa not in self._alerted_macs:
                self._seen_macs[sa].append(f["timestamp"])
                # Alert on 2nd attempt from same unknown MAC (1st could be coincidence)
                if len(self._seen_macs[sa]) >= 2:
                    self._alerted_macs.add(sa)
                    return {
                        "type": self.name,
                        "severity": self.severity,
                        "sourceMac": sa,
                        "targetMac": da or "Unknown",
                        "timestamp": now_str(),
                        "suggestion": self.suggestion,
                    }

        return None

    def reset(self):
        self._seen_macs.clear()
        self._alerted_macs.clear()
