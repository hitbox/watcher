from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import url_for

from . import extension
from . import views

def create_app():
    app = Flask(__name__)

    app.config.from_envvar('WATCHER_CONFIG')

    extension.init_app(app)
    views.init_app(app)

    @app.route('/')
    def index():
        return redirect(url_for('alerts.index'))

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

    return app
