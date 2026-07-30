import time
from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_DEAUTH, FC_BEACON, FC_PROBE_RESP
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

    # If beacon/probe frames outnumber deauth frames by this ratio,
    # it's a flood attack with incidental deauth — let FloodDetector handle it.
    FLOOD_SUPPRESSION_RATIO = 3

    def __init__(self):
        self._deauth_buckets = defaultdict(list)
        self._beacon_probe_count = defaultdict(list)
        self._alerted_macs = set()
        self._last_alert_time = {}

    def analyze(self, frames):
        now = time.time()
        cutoff = now - self.WINDOW_SECONDS

        # Count beacon/probe frames per source in the same window
        for f in frames:
            ft = f["frameType"]
            if ft in (FC_BEACON, FC_PROBE_RESP):
                sa = f.get("sa", "")
                if sa:
                    bp = self._beacon_probe_count[sa]
                    bp.append(now)
                    while bp and bp[0] < cutoff:
                        bp.pop(0)

        for f in frames:
            if f["frameType"] != FC_DEAUTH:
                continue
            sa = f.get("sa", "")
            if not sa:
                continue

            bucket = self._deauth_buckets[sa]
            bucket.append(now)
            # Prune old entries outside the window
            while bucket and bucket[0] < cutoff:
                bucket.pop(0)

            if len(bucket) >= self.DEAUTH_THRESHOLD:
                # Suppress if this source is predominantly sending beacon/probe
                # (indicates flood attack with incidental deauth frames)
                bp_count = len(self._beacon_probe_count.get(sa, []))
                if bp_count > len(bucket) * self.FLOOD_SUPPRESSION_RATIO:
                    continue

                last = self._last_alert_time.get(sa, 0)
                if now - last < self.COOLDOWN_SECONDS:
                    return None
                self._deauth_buckets[sa] = []
                self._last_alert_time[sa] = now
                da = f.get("da", "")
                # Deauth frames spoof AP's BSSID as source.
                # sourceMac: use a sentinel so topology can render attacker node
                # targetMac: the AP being attacked
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": "ff:ff:ff:00:00:01",
                    "targetMac": sa,
                    "timestamp": now_str(),
                    "suggestion": (
                        f"检测到Deauth泛洪攻击，攻击者伪造AP地址({sa})向"
                        f"{'所有客户端' if da == 'ff:ff:ff:ff:ff:ff' else da}"
                        f"发送大量去认证帧。{self.suggestion}"
                    ),
                }
        return None

    def reset(self):
        self._deauth_buckets.clear()
        self._alerted_macs.clear()
        self._last_alert_time.clear()
