from collections import defaultdict

from config import DETECTION_INTERVAL
from detection.base import BaseDetector
from detection.packet_reader import FC_BEACON, FC_PROBE_RESP
from utils.time_utils import now_str


def _oui(mac):
    return mac[:8] if len(mac) >= 8 else ""


def _is_local_admin_mac(mac):
    try:
        first_octet = int(mac.split(":")[0], 16)
    except (ValueError, IndexError):
        return False
    return bool(first_octet & 0x02)


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
        self._bssid_info = {}
        self._ssid_ref_bssid = {}
        self._alerted_ssids = set()
        self._beacon_count = defaultdict(int)
        self._beacon_rate_alerted = set()
        self._target_bssids = set()
        self._tick_count = 0
        self._beacon_reset_ticks = 5
        self._beacon_threshold = DETECTION_INTERVAL * 13 * self._beacon_reset_ticks

    def set_target_bssids(self, bssids):
        self._target_bssids = {b.lower() for b in bssids if b}

    def analyze(self, frames):
        for f in frames:
            if f["frameType"] == FC_BEACON:
                bssid = f.get("bssid", "") or f.get("sa", "")
                if bssid:
                    self._beacon_count[bssid] += 1

        result = self._check_ssid_collision(frames)
        if result:
            self._beacon_count.clear()
            self._tick_count = 0
            return result

        self._tick_count += 1
        if self._tick_count >= self._beacon_reset_ticks:
            result = self._check_beacon_rate_anomaly()
            self._beacon_count.clear()
            self._tick_count = 0
            if result:
                return result

        return None

    def _check_ssid_collision(self, frames):
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

            if bssid not in self._bssid_info:
                self._bssid_info[bssid] = {
                    "pairwiseCipher": f.get("pairwiseCipher", ""),
                    "groupCipher": f.get("groupCipher", ""),
                    "akm": f.get("akm", ""),
                    "channel": f.get("channel", ""),
                    "frequency": f.get("frequency", ""),
                    "signal": f.get("signal"),
                    "pmfCapable": f.get("pmfCapable", ""),
                    "pmfRequired": f.get("pmfRequired", ""),
                }

            if ssid_key not in self._ssid_ref_bssid:
                self._ssid_ref_bssid[ssid_key] = bssid

            bssids = self._ssid_bssids[ssid_key]
            if len(bssids) >= 2 and ssid_key not in self._alerted_ssids:
                ref_bssid = self._choose_reference_bssid(ssid_key, bssids)
                reasons = []

                for other in bssids:
                    if other == ref_bssid:
                        continue
                    ref_info = self._bssid_info.get(ref_bssid, {})
                    other_info = self._bssid_info.get(other, {})

                    ref_oui = _oui(ref_bssid)
                    other_oui = _oui(other)
                    if ref_oui and other_oui and ref_oui != other_oui:
                        reasons.append("供应商OUI不匹配 ({} vs {})".format(other_oui, ref_oui))

                    if _is_local_admin_mac(other) and other not in self._target_bssids:
                        reasons.append("{} 使用本地管理MAC，疑似伪造BSSID".format(other))

                    pc_ref = ref_info.get("pairwiseCipher", "")
                    pc_other = other_info.get("pairwiseCipher", "")
                    if pc_ref and pc_other and pc_ref != pc_other:
                        reasons.append("加密套件不匹配 ({} vs {})".format(pc_other, pc_ref))

                    gc_ref = ref_info.get("groupCipher", "")
                    gc_other = other_info.get("groupCipher", "")
                    if gc_ref and gc_other and gc_ref != gc_other:
                        reasons.append("组加密不匹配 ({} vs {})".format(gc_other, gc_ref))

                    akm_ref = ref_info.get("akm", "")
                    akm_other = other_info.get("akm", "")
                    if akm_ref and akm_other and akm_ref != akm_other:
                        reasons.append("认证方式不匹配 ({} vs {})".format(akm_other, akm_ref))

                    pmf_ref = ref_info.get("pmfRequired", "") or ref_info.get("pmfCapable", "")
                    pmf_other = other_info.get("pmfRequired", "") or other_info.get("pmfCapable", "")
                    if pmf_ref and pmf_other and pmf_ref != pmf_other:
                        reasons.append("PMF配置不匹配 ({} vs {})".format(pmf_other, pmf_ref))

                    channel_ref = ref_info.get("channel", "")
                    channel_other = other_info.get("channel", "")
                    if channel_ref and channel_other and channel_ref != channel_other:
                        reasons.append("信道不匹配 ({} vs {})".format(channel_other, channel_ref))

                    sig_ref = ref_info.get("signal")
                    sig_other = other_info.get("signal")
                    if sig_ref is not None and sig_other is not None and abs(sig_ref - sig_other) >= 25:
                        reasons.append("信号强度差异异常 ({}dBm vs {}dBm)".format(sig_other, sig_ref))

                    if self._target_bssids and other not in self._target_bssids:
                        reasons.append("{} 不在合法BSSID集合中".format(other))

                self._alerted_ssids.add(ssid_key)
                bssid_list = ", ".join(sorted(bssids))
                extra = "；".join(reasons) if reasons else "多个BSSID广播同一SSID"
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": list(bssids)[1],
                    "targetMac": list(bssids)[0],
                    "timestamp": now_str(),
                    "suggestion": (
                        "{} 检测到SSID '{}' 由多个BSSID广播: {}。{}".format(
                            self.suggestion, ssid_key, bssid_list, extra
                        )
                    ),
                }

        return None

    def _choose_reference_bssid(self, ssid_key, bssids):
        for bssid in bssids:
            if bssid in self._target_bssids:
                return bssid
        return self._ssid_ref_bssid[ssid_key]

    def _check_beacon_rate_anomaly(self):
        for bssid, count in list(self._beacon_count.items()):
            if count >= self._beacon_threshold and bssid not in self._beacon_rate_alerted:
                self._beacon_rate_alerted.add(bssid)
                return {
                    "type": self.name,
                    "severity": self.severity,
                    "sourceMac": bssid,
                    "targetMac": "",
                    "timestamp": now_str(),
                    "suggestion": (
                        "检测到BSSID {} 的Beacon帧频率异常偏高（{} 帧/检测周期，"
                        "阈值 {}），可能存在使用BSSID欺骗的钓鱼AP设备（如airbase-ng）。"
                        "该设备伪装成合法AP使用相同BSSID进行广播。"
                        "请立即断开连接并验证AP是否为合法设备。"
                    ).format(bssid, count, self._beacon_threshold),
                }
        return None

    def reset(self):
        self._ssid_bssids.clear()
        self._bssid_info.clear()
        self._ssid_ref_bssid.clear()
        self._alerted_ssids.clear()
        self._beacon_count.clear()
        self._beacon_rate_alerted.clear()
        self._target_bssids.clear()
        self._tick_count = 0
