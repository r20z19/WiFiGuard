import time
from collections import defaultdict

from detection.base import BaseDetector
from detection.packet_reader import FC_PROBE_RESP, FC_BEACON, FC_DEAUTH
from utils.time_utils import now_str


class FloodDetector(BaseDetector):
    name = "Flood泛洪"
    severity = "medium"
    suggestion = (
        "检测到无线泛洪攻击，网络中存在异常高频率的管理帧传输。"
        "建议启用AP的速率限制功能，检查异常高流量设备的合法性，"
        "必要时使用WIPS（无线入侵防御系统）进行自动阻断。"
    )

    # Per-source thresholds
    PROBE_RESP_THRESHOLD = 100   # >100 probe resp from same MAC in 1s
    MGMT_FLOOD_THRESHOLD = 200   # >200 mgmt frames from same MAC in 1s

    # Global threshold (catches random-MAC beacon flood like mdk4 b mode)
    GLOBAL_BEACON_THRESHOLD = 300  # >300 beacon/probe frames total in 1s
    GLOBAL_WINDOW_SECONDS = 1

    WINDOW_SECONDS = 1
    COOLDOWN_SECONDS = 60

    # Management frame types to count (exclude deauth - handled by DeauthDetector)
    MGMT_FRAME_TYPES = {FC_PROBE_RESP, FC_BEACON}

    def __init__(self):
        self._probe_buckets = defaultdict(list)
        self._mgmt_buckets = defaultdict(list)
        self._global_beacon_bucket = []
        self._alerted_macs = set()
        self._last_alert_time = {}

    def analyze(self, frames):
        now = time.time()
        cutoff = now - self.WINDOW_SECONDS
        global_cutoff = now - self.GLOBAL_WINDOW_SECONDS

        for f in frames:
            ft = f["frameType"]
            sa = f.get("sa", "")
            if not sa:
                continue

            # Per-source probe response detection
            if ft == FC_PROBE_RESP:
                pb = self._probe_buckets[sa]
                pb.append(now)
                while pb and pb[0] < cutoff:
                    pb.pop(0)
                if len(pb) >= self.PROBE_RESP_THRESHOLD:
                    if self._check_cooldown(sa, now):
                        return self._make_alert(sa, f.get("da", "Unknown"))

            # Per-source management frame detection
            if ft in self.MGMT_FRAME_TYPES:
                mb = self._mgmt_buckets[sa]
                mb.append(now)
                while mb and mb[0] < cutoff:
                    mb.pop(0)
                if len(mb) >= self.MGMT_FLOOD_THRESHOLD:
                    if self._check_cooldown(sa, now):
                        return self._make_alert(sa, f.get("da", "Unknown"))

                # Global beacon/probe counter (catches random-MAC floods)
                self._global_beacon_bucket.append(now)

        # Prune global bucket
        while self._global_beacon_bucket and self._global_beacon_bucket[0] < global_cutoff:
            self._global_beacon_bucket.pop(0)

        # Check global threshold
        if len(self._global_beacon_bucket) >= self.GLOBAL_BEACON_THRESHOLD:
            # Use a sentinel key for global cooldown
            if self._check_cooldown("__global_flood__", now):
                self._global_beacon_bucket.clear()
                return self._make_alert(
                    "ff:ff:ff:00:00:01",
                    "ff:ff:ff:ff:ff:ff",
                    detail="检测到大量伪造源地址的Beacon/Probe泛洪攻击。"
                )

        return None

    def _check_cooldown(self, sa, now):
        last = self._last_alert_time.get(sa, 0)
        if now - last < self.COOLDOWN_SECONDS:
            return False
        self._last_alert_time[sa] = now
        return True

    def _make_alert(self, sa, da, detail=None):
        return {
            "type": self.name,
            "severity": self.severity,
            "sourceMac": sa,
            "targetMac": da,
            "timestamp": now_str(),
            "suggestion": (detail + " " if detail else "") + self.suggestion,
        }

    def reset(self):
        self._probe_buckets.clear()
        self._mgmt_buckets.clear()
        self._global_beacon_bucket.clear()
        self._alerted_macs.clear()
        self._last_alert_time.clear()
