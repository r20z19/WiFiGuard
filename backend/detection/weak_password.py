import os
import re

from detection.base import BaseDetector
from utils.time_utils import now_str

# Path to hostapd config
HOSTAPD_CONF = "/etc/hostapd/wifiguard.conf"
# Path to rockyou dictionary (cleaned of control characters)
ROCKYOU_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rockyou_clean.txt")


def _get_ap_password():
    """Read the current AP password from hostapd config."""
    try:
        with open(HOSTAPD_CONF, "r") as f:
            for line in f:
                if line.startswith("wpa_passphrase="):
                    return line.strip().split("=", 1)[1]
    except (OSError, PermissionError):
        pass
    return None


def _check_complexity(password):
    """Check password complexity: must have at least 3 of 4 categories.

    Categories: uppercase, lowercase, digits, special characters.
    Returns (is_weak, reason).
    """
    if not password:
        return True, "密码为空"

    if len(password) < 8:
        return True, f"密码长度仅{len(password)}位，建议至少12位"

    categories = 0
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'[0-9]', password))
    has_special = bool(re.search(r'[^A-Za-z0-9]', password))

    categories = sum([has_upper, has_lower, has_digit, has_special])

    if categories < 3:
        missing = []
        if not has_upper:
            missing.append("大写字母")
        if not has_lower:
            missing.append("小写字母")
        if not has_digit:
            missing.append("数字")
        if not has_special:
            missing.append("特殊字符")
        return True, f"密码复杂度不足（缺少{'、'.join(missing)}），至少需要包含大写、小写、数字、特殊字符中的3种"

    return False, ""


def _check_in_rockyou(password):
    """Check if password exists in rockyou.txt dictionary.

    Uses grep -Fx for fast exact-line match on the cleaned dictionary file.
    """
    if not password or not os.path.exists(ROCKYOU_PATH):
        return False
    import subprocess
    try:
        result = subprocess.run(
            ["grep", "-qFx", password, ROCKYOU_PATH],
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


class WeakPasswordDetector(BaseDetector):
    name = "弱口令"
    severity = "medium"
    suggestion = (
        "建议使用包含大小写字母、数字和特殊字符的至少12位密码，"
        "且不要使用常见词汇或简单组合。"
    )

    def __init__(self):
        self._checked = False
        self._target_bssids = set()

    def set_target_bssids(self, bssids):
        self._target_bssids = {b.lower() for b in bssids if b}

    def analyze(self, frames):
        # Only check once per session
        if self._checked:
            return None
        self._checked = True

        password = _get_ap_password()
        if not password:
            return None

        # Check 1: Is the password in rockyou.txt?
        if _check_in_rockyou(password):
            ap_mac = ""
            try:
                from services.hostapd_service import get_status
                status = get_status()
                if status:
                    ap_mac = status.get("bssid[0]") or status.get("bssid") or ""
            except Exception:
                pass
            return {
                "type": self.name,
                "severity": "high",
                "sourceMac": ap_mac,
                "targetMac": "N/A",
                "timestamp": now_str(),
                "suggestion": (
                    f"当前AP密码属于黑客常用爆破字典(rockyou.txt)，极易被暴力破解！"
                    f"攻击者抓取握手包后可在数分钟内破解此密码。"
                    f"请立即更换为高强度密码。{self.suggestion}"
                ),
            }

        # Check 2: Password complexity (4 categories, need at least 3)
        is_weak, reason = _check_complexity(password)
        if is_weak:
            ap_mac = ""
            try:
                from services.hostapd_service import get_status
                status = get_status()
                if status:
                    ap_mac = status.get("bssid[0]") or status.get("bssid") or ""
            except Exception:
                pass
            return {
                "type": self.name,
                "severity": "medium",
                "sourceMac": ap_mac,
                "targetMac": "N/A",
                "timestamp": now_str(),
                "suggestion": (
                    f"当前AP密码强度不足：{reason}。"
                    f"弱密码容易被字典攻击或暴力破解。{self.suggestion}"
                ),
            }

        return None

    def reset(self):
        self._checked = False
