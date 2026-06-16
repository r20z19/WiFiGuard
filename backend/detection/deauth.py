import time
from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_DEAUTH
from utils.time_utils import now_str


class DeauthDetector(BaseDetector):
    name = "Deauth攻击"
    severity = "high"
    suggestion = (
        "检测到Deauth泛洪攻击，短时间内大量去认证帧被发送。"
        "建议启用802.11w PMF保护（Protected Management Frames），"
        "并检查AP是否配置了最大去认证速率限制。"
        "同时排查周边是否有可疑设备正在运行mdk4/aireplay-ng等攻击工具。"
    )

    # Threshold: >30 deauth frames from same MAC in a 10-second window
    DEAUTH_THRESHOLD = 30
    WINDOW_SECONDS = 10
    COOLDOWN_SECONDS = 60  # Don't re-alert same MAC within 60s

    def __init__(self):
        self._deauth_buckets = defaultdict(list)
        self._alerted_macs = set()
        self._last_alert_time = {}

    def analyze(self, frames):
        now = time.time()
        for f in frames:
            if f["frameType"] != FC_DEAUTH:
                continue
            sa = f.get("sa", "")
            if not sa:
                continue

            bucket = self._deauth_buckets[sa]
            bucket.append(now)
            # Prune old entries outside the window
            cutoff = now - self.WINDOW_SECONDS
            while bucket and bucket[0] < cutoff:
                bucket.pop(0)

            if len(bucket) >= self.DEAUTH_THRESHOLD:
                last = self._last_alert_time.get(sa, 0)
                if now - last < self.COOLDOWN_SECONDS:
                    return None
                self._deauth_buckets[sa] = []
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
        self._deauth_buckets.clear()
        self._alerted_macs.clear()
        self._last_alert_time.clear()
