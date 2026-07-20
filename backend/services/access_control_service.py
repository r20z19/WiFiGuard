import shutil
import subprocess
import time

from services.log_service import add_log
from config import (
    ACCESS_CONTROL_MODE,
    DEAUTH_COOLDOWN_SECONDS,
    DEAUTH_COUNT,
    MONITOR_INTERFACE,
)
from services.blacklist_service import get_mac_set as get_blacklist_macs
from services.whitelist_service import get_mac_set as get_whitelist_macs
from services.device_service import get_online_devices


class AccessController:
    """Enforce blacklist/whitelist policy by sending deauth frames on own BSS."""

    def __init__(self):
        self.mode = ACCESS_CONTROL_MODE
        self._last_kick = {}

    def enforce(self, devices, ap_bssids, scan_all=False):
        if self.mode not in ("blacklist", "whitelist"):
            return
        if not ap_bssids:
            return

        whitelist = get_whitelist_macs() if self.mode == "whitelist" else set()
        blacklist = get_blacklist_macs() if self.mode == "blacklist" else set()

        candidates = get_online_devices() if scan_all else devices
        for device in candidates:
            mac = (device.get("mac") or "").lower()
            if not mac or mac in ap_bssids:
                continue
            if self.mode == "blacklist":
                should_kick = mac in blacklist
            else:
                should_kick = mac not in whitelist
            if should_kick:
                self.kick(mac, device.get("bssid") or next(iter(ap_bssids)))

    def kick(self, client_mac, ap_bssid):
        now = time.time()
        key = (client_mac, ap_bssid)
        if now - self._last_kick.get(key, 0) < DEAUTH_COOLDOWN_SECONDS:
            return False
        self._last_kick[key] = now

        aireplay = shutil.which("aireplay-ng")
        if not aireplay:
            print("[准入控制] 需要安装 aircrack-ng 才能踢下线: {}".format(client_mac))
            return False

        cmd = [
            aireplay,
            "--deauth",
            str(DEAUTH_COUNT),
            "-a",
            ap_bssid,
            "-c",
            client_mac,
            MONITOR_INTERFACE,
        ]
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[准入控制] 已发送下线帧: client={} ap={} mode={}".format(
                client_mac, ap_bssid, self.mode
            ))
            add_log("WARNING", "device", f"设备被踢下线: {client_mac}", f"AP={ap_bssid} 模式={self.mode}")
            return True
        except OSError as exc:
            print("[准入控制] 踢下线失败 {}: {}".format(client_mac, exc))
            return False
