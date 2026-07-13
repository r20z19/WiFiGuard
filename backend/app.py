import os

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import SIMULATION_MODE
from database import init_db
from routes import register_routes

from detection.engine import DetectionEngine

from services.auth_service import require_auth


def create_app():
    app = Flask(__name__)
    CORS(app)
    init_db()
    register_routes(app)

    @app.before_request
    def check_auth():
        # Allow login endpoint without authentication
        if request.path == "/api/auth/login":
            return None

        # Only protect API routes
        if not request.path.startswith("/api/"):
            return None

        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return None

        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        # Auth sub-routes (verify, change-password) only need a valid token;
        # all other API routes also require the default password to be changed
        require_changed = not request.path.startswith("/api/auth/")

        payload, error = require_auth(token, require_changed)
        if error:
            return jsonify({"message": error}), 401

        # Store user info on request so routes can access it
        request.user_payload = payload

    return app


if __name__ == "__main__":
    app = create_app()

    engine = DetectionEngine()
    engine.start()

    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
