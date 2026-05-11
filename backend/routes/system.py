from flask import Blueprint, jsonify

from services.system_service import get_status

system_bp = Blueprint("system", __name__)


@system_bp.route("/api/system/status")
def system_status():
    return jsonify(get_status())
