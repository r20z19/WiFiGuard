"""Interface with hostapd via hostapd_cli for station management."""

import subprocess
import re


CTRL_INTERFACE = "/var/run/hostapd"
AP_INTERFACE = "wlan0"


def _run_cli(command):
    """Run a hostapd_cli command and return (success, output)."""
    cmd = ["hostapd_cli", "-i", AP_INTERFACE, "-p", CTRL_INTERFACE] + command.split()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[hostapd] 执行异常: {e}")
        return False, str(e)


def get_connected_stations():
    """Get list of currently connected stations (MAC addresses).

    Returns a list of dicts: [{"mac": "aa:bb:...", "connected_time": ...}, ...]
    """
    ok, output = _run_cli("all_sta")
    if not ok:
        return []

    stations = []
    current_mac = None
    current_info = {}

    for line in output.splitlines():
        line = line.strip()
        # MAC address line (starts a new station block)
        if re.match(r'^[0-9a-f]{2}(:[0-9a-f]{2}){5}$', line, re.IGNORECASE):
            if current_mac:
                stations.append(current_info)
            current_mac = line.lower()
            current_info = {"mac": current_mac}
        elif "=" in line and current_mac:
            key, _, value = line.partition("=")
            current_info[key.strip()] = value.strip()

    if current_mac:
        stations.append(current_info)

    return stations


def disconnect_station(mac):
    """Force disconnect a station from the AP.

    Uses hostapd_cli deauthenticate which sends a deauth frame
    and removes the station from hostapd's internal state.
    """
    mac = mac.strip().lower()
    ok, output = _run_cli(f"deauthenticate {mac}")
    if ok:
        print(f"[hostapd] 已断开站点: {mac}")
    else:
        print(f"[hostapd] 断开站点失败 {mac}: {output}")
    return ok


def deny_station(mac):
    """Deny a station by adding to hostapd deny ACL then deauthenticating.

    This ensures the station cannot re-associate after being kicked.
    """
    mac = mac.strip().lower()
    # Add to deny ACL first so device can't reconnect
    ok, output = _run_cli(f"deny_acl ADD_MAC {mac}")
    if ok:
        print(f"[hostapd] 已加入拒绝列表: {mac}")
    else:
        print(f"[hostapd] 加入拒绝列表失败 {mac}: {output}")
    # Then deauth to kick immediately
    disconnect_station(mac)
    return ok


def allow_station(mac):
    """Remove a station from the hostapd deny ACL.

    Call this when removing a device from the blacklist.
    """
    mac = mac.strip().lower()
    ok, output = _run_cli(f"deny_acl DEL_MAC {mac}")
    if ok:
        print(f"[hostapd] 已从拒绝列表移除: {mac}")
    else:
        print(f"[hostapd] 从拒绝列表移除失败 {mac}: {output}")
    return ok


def is_running():
    """Check if hostapd is running and responding."""
    ok, output = _run_cli("status")
    if not ok:
        return False
    return "state=ENABLED" in output


def get_status():
    """Get hostapd status info."""
    ok, output = _run_cli("status")
    if not ok:
        return None

    info = {}
    for line in output.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            info[key.strip()] = value.strip()
    return info
