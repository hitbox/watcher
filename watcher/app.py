from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for

from . import extension
from . import views
from .middleware import PrefixMiddleware

def create_app():
    app = Flask(__name__)

    app.config.from_envvar('WATCHER_CONFIG')

    extension.init_app(app)
    views.init_app(app)

    @app.route('/')
    def index():
        return redirect(url_for('alerts.index'))

    if app.debug:
        @app.route('/flash')
        def test_flash():
            """
            Test view all flash message types.
            """
            flash('Saved successfully!', 'success')
            flash('Something went wrong.', 'error')
            flash('Be careful with that.', 'warning')
            flash('FYI: settings updated.', 'info')
            return render_template('base.html')

    if 'PREFIX_URL' in app.config:
        # Prefix all urls for configuration
        prefix_url = app.config['PREFIX_URL']
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=prefix_url)

    return app
