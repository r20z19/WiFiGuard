from flask import Blueprint, jsonify, request, Response

from services.log_service import get_logs, get_log_stats, export_logs, add_log

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/api/logs")
def list_logs():
    level = request.args.get("level")
    category = request.args.get("category")
    search = request.args.get("search")
    limit = int(request.args.get("limit", 200))
    return jsonify(get_logs(level, category, search, limit))


@logs_bp.route("/api/logs/stats")
def stats():
    return jsonify(get_log_stats())


@logs_bp.route("/api/logs/export")
def export():
    level = request.args.get("level")
    category = request.args.get("category")
    search = request.args.get("search")
    logs = export_logs(level, category, search)

    # Build CSV
    header = "时间,等级,类别,消息,详情"
    rows = [header]
    for log in logs:
        detail = (log["detail"] or "").replace('"', '""')
        rows.append(
            f'"{log["timestamp"]}","{log["level"]}","{log["category"]}",'
            f'"{log["message"]}","{detail}"'
        )

    csv = "\n".join(rows)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=wifiguard-logs.csv"},
    )
