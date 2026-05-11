from flask import Blueprint, jsonify, request

from services.whitelist_service import get_all, add, remove
from utils.mac_utils import is_valid_mac, normalize_mac

whitelist_bp = Blueprint("whitelist", __name__)


@whitelist_bp.route("/api/devices/whitelist")
def list_whitelist():
    return jsonify(get_all())


@whitelist_bp.route("/api/devices/whitelist", methods=["POST"])
def add_to_whitelist():
    data = request.get_json()
    mac = normalize_mac(data.get("mac", ""))

    if not mac or not is_valid_mac(mac):
        return jsonify({"error": "无效的MAC地址"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "设备名称不能为空"}), 400

    add(mac, name)
    return jsonify({"success": True})


@whitelist_bp.route("/api/devices/whitelist/<path:mac>", methods=["DELETE"])
def remove_from_whitelist(mac):
    remove(normalize_mac(mac))
    return jsonify({"success": True})
