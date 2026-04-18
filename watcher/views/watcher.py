import logging

import click

from flask import Blueprint

from watcher.evaluate import evaluate_alerts
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
    evaluate_alerts(ignore_missing)
