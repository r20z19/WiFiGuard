import os

from flask import Flask
from flask_cors import CORS

from config import SIMULATION_MODE
from database import init_db
from routes import register_routes


def create_app():
    app = Flask(__name__)
    CORS(app)

    init_db()
    register_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()

    if SIMULATION_MODE:
        from detection.engine import DetectionEngine

        engine = DetectionEngine()
        engine.start()

    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
