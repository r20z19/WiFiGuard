from flask import Blueprint, jsonify, request

from services.blacklist_service import get_all, add, remove
from utils.mac_utils import is_valid_mac, normalize_mac

blacklist_bp = Blueprint("blacklist", __name__)


@blacklist_bp.route("/api/devices/blacklist")
def list_blacklist():
    return jsonify(get_all())


@blacklist_bp.route("/api/devices/blacklist", methods=["POST"])
def add_to_blacklist():
    data = request.get_json()
    mac = normalize_mac(data.get("mac", ""))

    if not mac or not is_valid_mac(mac):
        return jsonify({"error": "无效的MAC地址"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "设备名称不能为空"}), 400

    reason = data.get("reason", "").strip()
    add(mac, name, reason)
    return jsonify({"success": True})


@blacklist_bp.route("/api/devices/blacklist/<path:mac>", methods=["DELETE"])
def remove_from_blacklist(mac):
    remove(normalize_mac(mac))
    return jsonify({"success": True})
