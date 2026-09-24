from flask import flash
from flask import url_for
from watcher.navlink import NavLink
from markupsafe import Markup

from .alerts import alerts_bp
from .database import database_bp
from .watcher import watcher_bp

def init_app(app):
    app.register_blueprint(database_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(watcher_bp)

    @app.context_processor
    def inject():
        navigation = [
            NavLink(
                text = 'Alerts',
                endpoint = 'alerts.list',
                pattern = 'alerts\.',
            )
        ]

        if app.debug:
            navigation.append(NavLink(
                text = 'Flash Debug',
                endpoint = 'test_flash',
                pattern = 'test_flash',
            ))

        context = {
            'navigation': navigation,
        }
        return context
