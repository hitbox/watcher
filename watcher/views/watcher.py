import logging

import click

from flask import Blueprint

from watcher.extension import db
from watcher.models import Alert

watcher_bp = Blueprint('watcher', __name__)

alerts_bp = Blueprint('alerts', __name__)

watcher_bp.register_blueprint(alerts_bp)

logger = logging.getLogger(__name__)

@alerts_bp.cli.command('evaluate')
@click.option('--ignore-missing/--no-ignore-missing')
def evaluate(ignore_missing):
    """
    Harvest path stats and do alerts for conditions.
    """
    query = db.select(Alert)
    for alert in db.session.scalars(query):
        need_alerts = alert.alerts_for_paths(ignore_missing=ignore_missing)
        if not need_alerts:
            logger.info(f'no alerts for %s', alert.name)
        for alert, path_object in need_alerts:
            logger.info('Alert %s for %s', alert.name, path_object.path)
            alert.do_alert(path_object)
            db.session.commit()
