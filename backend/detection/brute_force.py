import time
from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_AUTH
from utils.time_utils import now_str


class BruteForceDetector(BaseDetector):
    name = "暴力破解"
    severity = "medium"
    suggestion = (
        "检测到WiFi暴力破解尝试，短时间内出现大量认证请求。"
        "建议启用WPA3-SAE（Simultaneous Authentication of Equals），"
        "或确保WPA2-PSK使用强密码，并配置AP的认证失败速率限制和锁定策略。"
    )

    # Threshold: >15 auth attempts from same client MAC in a 30-second window
    # Normal connections typically produce 1-3 auth frames; legitimate retries
    # (e.g. wrong password, signal loss) may produce up to 10.
    AUTH_THRESHOLD = 15
    WINDOW_SECONDS = 30
    COOLDOWN_SECONDS = 120

    def __init__(self):
        self._auth_buckets = defaultdict(list)
        self._alerted_macs = set()
        self._last_alert_time = {}
        self._ap_macs = set()

    def set_ap_macs(self, macs):
        """Set known AP MACs to exclude from detection (APs send auth responses)."""
        self._ap_macs = set(macs)

    def analyze(self, frames):
        now = time.time()
        for f in frames:
            if f["frameType"] != FC_AUTH:
                continue
            sa = f.get("sa", "")
            if not sa:
                continue

            # Skip auth frames sent by the AP (responses)
            if sa in self._ap_macs:
                continue

            bucket = self._auth_buckets[sa]
            bucket.append(now)
            cutoff = now - self.WINDOW_SECONDS
            while bucket and bucket[0] < cutoff:
                bucket.pop(0)

            if len(bucket) >= self.AUTH_THRESHOLD:
                last = self._last_alert_time.get(sa, 0)
                if now - last < self.COOLDOWN_SECONDS:
                    return None
                self._last_alert_time[sa] = now
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": sa,
                    "targetMac": f.get("da", "Unknown"),
                    "timestamp": now_str(),
                    "suggestion": self.suggestion,
                }

        return None

    def reset(self):
        self._auth_buckets.clear()
        self._alerted_macs.clear()
        self._last_alert_time.clear()
