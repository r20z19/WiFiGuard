import os
import logging

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from database import init_db
from routes import register_routes

from detection.engine import DetectionEngine


FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)


def create_app():
    static_folder = FRONTEND_DIST if os.path.isdir(FRONTEND_DIST) else None
    app = Flask(__name__, static_folder=None)
    CORS(app)
    init_db()
    register_routes(app)

    if static_folder:
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path.startswith("api/"):
                return jsonify({"error": "API endpoint not found"}), 404
            file_path = os.path.join(static_folder, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(static_folder, path)
            return send_from_directory(static_folder, "index.html")

    return app


if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    app = create_app()

    engine = DetectionEngine()
    engine.start()

    debug = os.environ.get("WIFIGUARD_DEBUG", "false").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=debug,
        use_reloader=False,
        threaded=True,
    )
