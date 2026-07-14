from detection.base import BaseDetector
from detection.packet_reader import FC_BEACON, FC_PROBE_RESP
from utils.time_utils import now_str


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

    def analyze(self, frames):
        for f in frames:
            if f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                continue
            bssid = f.get("bssid") or f.get("sa") or "N/A"
            if bssid in self._alerted_bssids:
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
        pmf_capable = str(frame.get("pmfCapable", "")).lower()
        pmf_required = str(frame.get("pmfRequired", "")).lower()

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

        if akm == "2" and pmf_capable in ("0", "false") and pmf_required in ("0", "false"):
            return "WPA2-PSK未启用PMF"
        return ""

    def reset(self):
        self._alerted_bssids.clear()
