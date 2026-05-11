from routes.system import system_bp
from routes.alerts import alerts_bp
from routes.devices import devices_bp
from routes.whitelist import whitelist_bp
from routes.blacklist import blacklist_bp
from routes.email import email_bp


def register_routes(app):
    app.register_blueprint(system_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(whitelist_bp)
    app.register_blueprint(blacklist_bp)
    app.register_blueprint(email_bp)
