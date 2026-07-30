import time
from collections import defaultdict

import config
from detection.base import BaseDetector
from detection.packet_reader import FC_AUTH, FC_ASSOC_REQ, FC_ASSOC_RESP
from services.whitelist_service import get_mac_set as get_whitelist_macs
from services.blacklist_service import get_mac_set as get_blacklist_macs
from utils.time_utils import now_str


class IllegalAccessDetector(BaseDetector):
    name = "非法接入"
    severity = "high"
    suggestion = (
        "检测到未授权设备接入网络。该设备不在白名单中，已被限制访问互联网。"
        "如果是合法设备，请在管理界面将其加入白名单以授权上网；"
        "如果是可疑设备，建议将其加入黑名单以彻底阻断连接。"
    )

    # Alert once per unknown MAC, then cooldown
    COOLDOWN_SECONDS = 300  # Don't re-alert same MAC within 5 minutes

    def __init__(self, known_macs=None):
        self._ap_macs = set()
        self._target_bssids = set()
        self._last_alert_time = {}

    def set_ap_macs(self, macs):
        self._ap_macs = set(macs)

    def set_target_bssids(self, bssids):
        self._target_bssids = {b.lower() for b in bssids if b}

    def set_known_macs(self, macs):
        # Legacy interface — whitelist is now the source of truth
        pass

    def add_known_mac(self, mac):
        pass

    def analyze(self, frames):
        # Only produce alerts when relevant modes are enabled
        whitelist_on = config.WHITELIST_ENABLED
        blacklist_on = config.BLACKLIST_ENABLED

        if not whitelist_on and not blacklist_on:
            return None  # No access control active, no illegal-access alerts

        now = time.time()
        whitelist = get_whitelist_macs() if whitelist_on else set()
        blacklist = get_blacklist_macs() if blacklist_on else set()

        for f in frames:
            ft = f["frameType"]
            # Only look at auth and association request frames
            if ft not in (FC_AUTH, FC_ASSOC_REQ):
                continue

            sa = f.get("sa", "")
            da = f.get("da", "")
            bssid = f.get("bssid", "")

            if not sa:
                continue

            # Skip AP's own MAC
            if sa in self._ap_macs:
                continue

            # Only care about frames directed at our AP
            target = da or bssid or ""
            if self._target_bssids and target not in self._target_bssids:
                continue
            if self._ap_macs and target not in self._ap_macs:
                continue

            # Skip if device is in whitelist (authorized)
            if whitelist_on and sa in whitelist:
                continue

            # Cooldown check
            last = self._last_alert_time.get(sa, 0)
            if now - last < self.COOLDOWN_SECONDS:
                continue

            self._last_alert_time[sa] = now

            # Determine severity and alert based on list status
            if blacklist_on and sa in blacklist:
                detail = "黑名单设备尝试重新接入，已被自动阻断。"
                severity = "critical"
            elif whitelist_on:
                # Whitelist is on and device is not in whitelist — unauthorized
                detail = (
                    f"未授权设备 {sa} 接入WiFi网络，已自动限制其互联网访问。"
                    f"请确认是否为合法设备。"
                )
                severity = "high"
            else:
                # Only blacklist mode is on, device is not blacklisted — skip
                continue

            return {
                "type": self.name,
                "severity": severity,
                "sourceMac": sa,
                "targetMac": da or bssid or "Unknown",
                "timestamp": now_str(),
                "suggestion": detail + " " + self.suggestion,
            }

        return None

    def reset(self):
        self._last_alert_time.clear()
