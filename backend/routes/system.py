from flask import Blueprint, jsonify, request

import config
from services.system_service import get_status

system_bp = Blueprint("system", __name__)


@system_bp.route("/api/system/status")
def system_status():
    return jsonify(get_status())


@system_bp.route("/api/system/access-mode", methods=["PUT"])
def update_access_mode():
    """Dynamically toggle whitelist/blacklist enforcement."""
    data = request.get_json()

    if "whitelistEnabled" in data:
        config.WHITELIST_ENABLED = bool(data["whitelistEnabled"])
    if "blacklistEnabled" in data:
        config.BLACKLIST_ENABLED = bool(data["blacklistEnabled"])

    # Sync nftables state according to new settings
    _sync_nftables_state()

    return jsonify({
        "success": True,
        "whitelistEnabled": config.WHITELIST_ENABLED,
        "blacklistEnabled": config.BLACKLIST_ENABLED,
    })


def _sync_nftables_state():
    """Sync nftables rules to match current config toggles."""
    try:
        from services.nftables_service import (
            sync_from_whitelist, sync_from_blacklist,
            flush_trusted, flush_blocked,
            set_forward_policy,
        )
        from services.whitelist_service import get_mac_set as get_wl_macs
        from services.blacklist_service import get_mac_set as get_bl_macs

        if config.WHITELIST_ENABLED:
            # Restore drop policy + sync whitelist to trusted set
            set_forward_policy("drop")
            sync_from_whitelist(get_wl_macs())
        else:
            # Allow all forwarding, clear trusted set (not needed)
            set_forward_policy("accept")
            flush_trusted()

        if config.BLACKLIST_ENABLED:
            sync_from_blacklist(get_bl_macs())
        else:
            flush_blocked()

    except Exception as e:
        print(f"[access-mode] nftables同步失败: {e}")
