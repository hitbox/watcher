from .database import database_bp
from .watcher import watcher_bp
from .alerts import alerts_bp

def init_app(app):
    app.register_blueprint(database_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(watcher_bp)
