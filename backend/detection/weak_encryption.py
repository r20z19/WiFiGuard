import os

from detection.base import BaseDetector
from detection.packet_reader import FC_BEACON, FC_PROBE_RESP
from utils.time_utils import now_str

HOSTAPD_CONF = "/etc/hostapd/wifiguard.conf"


def _read_hostapd_pmf():
    """直接读 hostapd 配置文件判断 PMF 是否开启，比解析 beacon 可靠"""
    try:
        with open(HOSTAPD_CONF) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ieee80211w="):
                    val = line.split("=", 1)[1].strip()
                    return int(val) >= 1
    except (OSError, ValueError):
        pass
    return False


class WeakEncryptionDetector(BaseDetector):
    name = "弱加密协议"
    severity = "medium"
    suggestion = (
        "检测到WiFi使用弱加密或缺少管理帧保护。建议关闭开放网络、WEP、WPA1和TKIP，"
        "优先使用WPA3-SAE；若只能使用WPA2，请选择AES/CCMP并开启PMF。"
    )

    WEAK_CIPHER_TYPES = {"1": "WEP40", "2": "TKIP", "5": "WEP104"}

    def __init__(self):
        self._alerted_bssids = set()
        self._target_bssids = set()

    def set_target_bssids(self, bssids):
        """Only alert on weak encryption for our own AP, not neighbors."""
        self._target_bssids = {b.lower() for b in bssids if b}

    def analyze(self, frames):
        for f in frames:
            if f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                continue
            bssid = (f.get("bssid") or f.get("sa") or "").lower()
            if not bssid or bssid == "n/a":
                continue
            if bssid in self._alerted_bssids:
                continue

            # Only check our own AP for weak encryption, not neighbor networks
            if self._target_bssids and bssid not in self._target_bssids:
                continue

            reason = self._weak_reason(f)
            if not reason:
                continue

            self._alerted_bssids.add(bssid)
            ssid = f.get("ssid", "")
            return {
                "type": self.name,
                "severity": self.severity,
                "sourceMac": bssid,
                "targetMac": "N/A",
                "timestamp": now_str(),
                "suggestion": "SSID '{}' 存在弱加密风险：{}。{}".format(
                    ssid or "隐藏SSID", reason, self.suggestion
                ),
            }
        return None

    def _weak_reason(self, frame):
        info = frame.get("info", "")
        privacy = frame.get("privacy", "")
        group_cipher = str(frame.get("groupCipher", ""))
        pairwise_cipher = str(frame.get("pairwiseCipher", ""))
        akm = str(frame.get("akm", ""))

        if privacy == "0":
            return "开放网络未启用加密"
        if "WEP" in info:
            return "使用WEP"
        if "WPA Version" in info and "RSN" not in info:
            return "使用WPA1"

        weak = []
        for value in (group_cipher, pairwise_cipher):
            if value in self.WEAK_CIPHER_TYPES:
                weak.append(self.WEAK_CIPHER_TYPES[value])
        if weak:
            return "使用{}".format("/".join(sorted(set(weak))))

        # WPA2-PSK: 直接读 hostapd 配置判断 PMF
        if akm == "2":
            if not _read_hostapd_pmf():
                return "WPA2-PSK未启用PMF（管理帧保护）"
        return ""

    def reset(self):
        self._alerted_bssids.clear()
