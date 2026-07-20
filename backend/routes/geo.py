from flask import Blueprint, jsonify, request

from services.geo_service import get_network_locations, geolocate_ip

geo_bp = Blueprint("geo", __name__)


@geo_bp.route("/api/geo/locations")
def network_locations():
    """Return all devices and alerts with geographic coordinates."""
    return jsonify(get_network_locations())


@geo_bp.route("/api/geo/ip")
def ip_location():
    """Resolve a single IP address to geographic coordinates."""
    ip = request.args.get("ip", "")
    if not ip:
        return jsonify({"error": "Missing ip parameter"}), 400
    result = geolocate_ip(ip)
    if result is None:
        return jsonify({"error": "Could not resolve IP"}), 404
    return jsonify(result)
