import os
import logging

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from database import init_db
from routes import register_routes

from detection.engine import DetectionEngine

from services.auth_service import require_auth


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

    # Sync whitelist/blacklist to nftables on startup
    try:
        from services.nftables_service import (
            sync_from_whitelist, sync_from_blacklist,
            flush_trusted, flush_blocked, set_forward_policy,
        )
        from services.whitelist_service import get_mac_set as get_wl_macs
        from services.blacklist_service import get_mac_set as get_bl_macs
        import config

        if config.WHITELIST_ENABLED:
            set_forward_policy("drop")
            added, removed = sync_from_whitelist(get_wl_macs())
            print(f"[nftables] 白名单同步: +{added} -{removed}")
        else:
            set_forward_policy("accept")
            flush_trusted()
            print("[nftables] 白名单未启用，转发策略: accept")

        if config.BLACKLIST_ENABLED:
            added, removed = sync_from_blacklist(get_bl_macs())
            print(f"[nftables] 黑名单同步: +{added} -{removed}")
            # Sync hostapd deny ACL
            from services.hostapd_service import deny_station
            for mac in get_bl_macs():
                deny_station(mac)
            print(f"[hostapd] 黑名单ACL同步: {len(get_bl_macs())} 个设备")
        else:
            flush_blocked()
            print("[nftables] 黑名单未启用，已清空封锁集合")
    except Exception as e:
        print(f"[nftables] 启动同步失败 (非致命): {e}")

    engine = DetectionEngine()
    from services.log_service import add_log
    add_log("INFO", "system", "系统启动", f"模式: {'模拟' if os.environ.get('WIFIGUARD_SIM','true')=='true' else '监听'}")
    engine.start()

    debug = os.environ.get("WIFIGUARD_DEBUG", "false").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=debug,
        use_reloader=False,
        threaded=True,
    )
