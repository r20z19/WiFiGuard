from flask import Blueprint, jsonify

from services.device_service import get_online_devices

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/api/devices/online")
def online_devices():
    return jsonify(get_online_devices())
