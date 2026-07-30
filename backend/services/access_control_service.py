import time

from services.log_service import add_log
import config
from config import DEAUTH_COOLDOWN_SECONDS
from services.blacklist_service import get_mac_set as get_blacklist_macs
from services.whitelist_service import get_mac_set as get_whitelist_macs
from services.device_service import get_online_devices
from services.nftables_service import add_blocked, add_trusted, remove_trusted
from services.hostapd_service import deny_station


class AccessController:
    """Enforce access control policy via hostapd + nftables.

    Two independent toggles:
    - WHITELIST_ENABLED: only whitelisted MACs can reach the internet.
      Strangers can associate to AP but nftables drops their forwarding.
    - BLACKLIST_ENABLED: blacklisted MACs are kicked from the AP and
      blocked at the firewall level.

    Combinations:
    - Both off:  all devices freely connect and use internet.
    - Whitelist only: strangers can connect but not use internet; alerts raised.
    - Blacklist only: all devices free except blacklisted ones get kicked.
    - Both on: only whitelist can internet, blacklist gets kicked, strangers
      can connect but no internet + alerts.
    """

    def __init__(self):
        self._last_kick = {}

    def enforce(self, devices, ap_bssids, scan_all=False):
        """Enforce access policy on currently connected devices."""
        whitelist_on = config.WHITELIST_ENABLED
        blacklist_on = config.BLACKLIST_ENABLED

        if not whitelist_on and not blacklist_on:
            return  # Free mode — no enforcement

        blacklist = get_blacklist_macs() if blacklist_on else set()
        whitelist = get_whitelist_macs() if whitelist_on else set()

        candidates = get_online_devices() if scan_all else devices
        for device in candidates:
            mac = (device.get("mac") or "").lower()
            if not mac or mac in ap_bssids:
                continue

            if blacklist_on and mac in blacklist:
                # Blacklisted: kick and block completely
                self._kick(mac)
            elif whitelist_on and mac in whitelist:
                # Whitelisted: ensure they can reach internet
                add_trusted(mac)
            elif whitelist_on:
                # Whitelist mode active, stranger: no internet
                remove_trusted(mac)
            # If only blacklist mode and device is not blacklisted: do nothing (free access)

    def _kick(self, client_mac):
        """Disconnect and block a client using hostapd + nftables."""
        now = time.time()
        if now - self._last_kick.get(client_mac, 0) < DEAUTH_COOLDOWN_SECONDS:
            return False
        self._last_kick[client_mac] = now

        # Layer 1: nftables - block at forwarding level
        add_blocked(client_mac)

        # Layer 2: hostapd - add to deny ACL + force deauthentication
        deny_station(client_mac)

        print("[准入控制] 黑名单阻断: client={}".format(client_mac))
        add_log(
            "WARNING", "device",
            f"黑名单设备被阻断: {client_mac}",
            "hostapd断开 + nftables封锁"
        )
        return True
