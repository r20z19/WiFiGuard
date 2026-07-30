"""Manage nftables trusted_macs and blocked_macs sets for network access control."""

import subprocess
import shlex


TABLE = "inet wifiguard"
TRUSTED_SET = "trusted_macs"
BLOCKED_SET = "blocked_macs"


def _run_nft(cmd):
    """Execute an nft command. Returns (success, output)."""
    full_cmd = f"nft {cmd}"
    try:
        result = subprocess.run(
            shlex.split(full_cmd),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print(f"[nftables] 命令失败: {full_cmd}\n  {result.stderr.strip()}")
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[nftables] 执行异常: {e}")
        return False, str(e)


def _validate_mac(mac):
    """Basic MAC address validation."""
    mac = mac.strip().lower()
    parts = mac.split(":")
    if len(parts) != 6:
        return None
    for p in parts:
        if len(p) != 2:
            return None
        try:
            int(p, 16)
        except ValueError:
            return None
    return mac


def add_trusted(mac):
    """Add a MAC to the trusted set (allow internet forwarding)."""
    mac = _validate_mac(mac)
    if not mac:
        return False
    ok, _ = _run_nft(f'add element {TABLE} {TRUSTED_SET} {{ {mac} }}')
    if ok:
        print(f"[nftables] 已添加可信设备: {mac}")
    return ok


def remove_trusted(mac):
    """Remove a MAC from the trusted set."""
    mac = _validate_mac(mac)
    if not mac:
        return False
    ok, _ = _run_nft(f'delete element {TABLE} {TRUSTED_SET} {{ {mac} }}')
    if ok:
        print(f"[nftables] 已移除可信设备: {mac}")
    return ok


def add_blocked(mac):
    """Add a MAC to the blocked set (drop all traffic)."""
    mac = _validate_mac(mac)
    if not mac:
        return False
    # Also remove from trusted if present
    remove_trusted(mac)
    ok, _ = _run_nft(f'add element {TABLE} {BLOCKED_SET} {{ {mac} }}')
    if ok:
        print(f"[nftables] 已封锁设备: {mac}")
    return ok


def remove_blocked(mac):
    """Remove a MAC from the blocked set."""
    mac = _validate_mac(mac)
    if not mac:
        return False
    ok, _ = _run_nft(f'delete element {TABLE} {BLOCKED_SET} {{ {mac} }}')
    if ok:
        print(f"[nftables] 已解封设备: {mac}")
    return ok


def list_trusted():
    """Return set of MACs currently in trusted_macs."""
    ok, output = _run_nft(f'list set {TABLE} {TRUSTED_SET}')
    if not ok:
        return set()
    return _parse_set_output(output)


def list_blocked():
    """Return set of MACs currently in blocked_macs."""
    ok, output = _run_nft(f'list set {TABLE} {BLOCKED_SET}')
    if not ok:
        return set()
    return _parse_set_output(output)


def _parse_set_output(output):
    """Parse nft list set output to extract MAC addresses."""
    macs = set()
    in_elements = False
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("elements"):
            in_elements = True
            # elements = { aa:bb:cc:dd:ee:ff, ... }
            content = line.split("=", 1)[-1].strip().strip("{}")
            for part in content.split(","):
                mac = part.strip()
                if mac and ":" in mac:
                    macs.add(mac.lower())
    return macs


def sync_from_whitelist(whitelist_macs):
    """Sync the trusted_macs set to match the given whitelist.

    Adds MACs not yet in the set, removes MACs no longer in the list.
    """
    current = list_trusted()
    target = {m.lower() for m in whitelist_macs if _validate_mac(m)}

    to_add = target - current
    to_remove = current - target

    for mac in to_add:
        add_trusted(mac)
    for mac in to_remove:
        remove_trusted(mac)

    return len(to_add), len(to_remove)


def sync_from_blacklist(blacklist_macs):
    """Sync the blocked_macs set to match the given blacklist."""
    current = list_blocked()
    target = {m.lower() for m in blacklist_macs if _validate_mac(m)}

    to_add = target - current
    to_remove = current - target

    for mac in to_add:
        add_blocked(mac)
    for mac in to_remove:
        remove_blocked(mac)

    return len(to_add), len(to_remove)


def flush_trusted():
    """Remove all MACs from the trusted set."""
    ok, _ = _run_nft(f'flush set {TABLE} {TRUSTED_SET}')
    if ok:
        print("[nftables] 已清空可信设备集合")
    return ok


def flush_blocked():
    """Remove all MACs from the blocked set."""
    ok, _ = _run_nft(f'flush set {TABLE} {BLOCKED_SET}')
    if ok:
        print("[nftables] 已清空封锁设备集合")
    return ok


def set_forward_policy(policy):
    """Set the forward chain default policy (accept or drop).

    - 'accept': all devices can reach internet (no whitelist enforcement)
    - 'drop': only trusted_macs can forward (whitelist enforcement active)
    """
    if policy not in ("accept", "drop"):
        return False
    ok, _ = _run_nft(f'chain {TABLE} forward {{ policy {policy} ; }}')
    if not ok:
        # Fallback: try using the full add command syntax
        ok, _ = _run_nft(
            f'add chain {TABLE} forward {{ type filter hook forward priority 0 ; policy {policy} ; }}'
        )
    if ok:
        print(f"[nftables] 转发策略已设为: {policy}")
    return ok
