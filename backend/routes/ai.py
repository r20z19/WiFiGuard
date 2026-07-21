import json
from flask import Blueprint, jsonify, request

from services.frame_service import get_attack_context, get_frame_summary
from services.ai_service import (
    get_config,
    save_config,
    interpret_alert,
    chat_with_context,
    generate_report,
    identify_device,
    detect_anomalies,
    predict_threats,
)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/api/ai/config", methods=["GET"])
def ai_get_config():
    cfg = get_config()
    return jsonify({
        "provider": cfg["provider"],
        "hasKey": bool(cfg["apiKey"]),
        "enabled": cfg["enabled"],
    })


@ai_bp.route("/api/ai/config", methods=["POST"])
def ai_save_config():
    data = request.get_json() or {}
    provider = data.get("provider", "deepseek")
    api_key = data.get("apiKey", "")
    enabled = data.get("enabled", False)
    cfg = save_config(provider, api_key, enabled)
    return jsonify({
        "provider": cfg["provider"],
        "hasKey": bool(cfg["apiKey"]),
        "enabled": cfg["enabled"],
    })


@ai_bp.route("/api/ai/interpret", methods=["POST"])
def ai_interpret():
    data = request.get_json() or {}
    alert = {
        "type": data.get("type", ""),
        "severity": data.get("severity", ""),
        "sourceMac": data.get("sourceMac", ""),
        "targetMac": data.get("targetMac", ""),
        "timestamp": data.get("timestamp", ""),
        "suggestion": data.get("suggestion", ""),
    }
    # Get frame context if available
    frames = None
    source_mac = alert.get("sourceMac") or alert.get("source_mac")
    if source_mac:
        frames = get_attack_context(source_mac)
    result, error = interpret_alert(alert, frames)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})


@ai_bp.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.get_json() or {}
    messages = data.get("messages", [])
    context = data.get("context", "")
    result, error = chat_with_context(messages, context)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})


@ai_bp.route("/api/ai/report", methods=["POST"])
def ai_report():
    data = request.get_json() or {}
    summary = data.get("summary", {})
    result, error = generate_report(summary)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})


@ai_bp.route("/api/ai/identify", methods=["POST"])
def ai_identify():
    data = request.get_json() or {}
    device = data.get("device", {})
    result, error = identify_device(device)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})


def _extract_json(text):
    """Extract JSON from AI response (may be wrapped in markdown code blocks)."""
    if not isinstance(text, str):
        return text
    t = text.strip()
    # Remove markdown code fences (```json ... ``` or ``` ... ```)
    import re
    # Try to extract content between code fences
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', t, re.DOTALL)
    if m:
        t = m.group(1).strip()
    # Find the outermost JSON object or array
    # Try matching balanced braces
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = t.find(start_char)
        if start < 0:
            continue
        depth = 0
        end = start
        for i in range(start, len(t)):
            if t[i] == start_char:
                depth += 1
            elif t[i] == end_char:
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if depth == 0:
            try:
                return json.loads(t[start:end])
            except Exception:
                continue
    # Fallback: try loading the whole thing
    try:
        return json.loads(t)
    except Exception:
        return text


@ai_bp.route("/api/ai/anomalies", methods=["POST"])
def ai_anomalies():
    data = request.get_json() or {}
    devices = data.get("devices", [])
    result, error = detect_anomalies(devices)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": _extract_json(result)})


@ai_bp.route("/api/ai/predict", methods=["POST"])
def ai_predict():
    data = request.get_json() or {}
    current = data.get("current", {})
    result, error = predict_threats(current)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": _extract_json(result)})


@ai_bp.route("/api/ai/frames")
def ai_frames():
    """Get recent frame activity context for AI analysis."""
    mac = request.args.get("mac", "")
    if mac:
        ctx = get_attack_context(mac)
    else:
        ctx = get_frame_summary(limit=30)
    return jsonify(ctx)
