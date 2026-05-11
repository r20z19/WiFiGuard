from flask import Blueprint, jsonify, request

from services.email_service import get_config, update_config, send_test, get_records

email_bp = Blueprint("email", __name__)


@email_bp.route("/api/email/config")
def email_config():
    return jsonify(get_config())


@email_bp.route("/api/email/config", methods=["PUT"])
def update_email_config():
    data = request.get_json() or {}
    updated = update_config(data)
    return jsonify(updated)


@email_bp.route("/api/email/test", methods=["POST"])
def test_email():
    data = request.get_json() or {}
    success, message = send_test(data)
    return jsonify({"success": success, "message": message})


@email_bp.route("/api/email/records")
def email_records():
    return jsonify(get_records())
