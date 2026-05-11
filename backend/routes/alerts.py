from flask import Blueprint, jsonify, request

from services.alert_service import get_current_alerts, get_history_alerts, clear_alert

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/api/alerts/current")
def current_alerts():
    return jsonify(get_current_alerts())


@alerts_bp.route("/api/alerts/history")
def history_alerts():
    alert_type = request.args.get("type")
    status = request.args.get("status")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    return jsonify(get_history_alerts(alert_type, status, start_date, end_date))


@alerts_bp.route("/api/alerts/<int:alert_id>/clear", methods=["POST"])
def clear_single_alert(alert_id):
    success = clear_alert(alert_id)
    if not success:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"success": True})
