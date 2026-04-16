import click

from flask import Blueprint

from watcher.extension import db

from watcher.models import Alert
from watcher.models import ConditionGroup
from watcher.models import ConditionLeaf
from watcher.models import ConditionNode
from watcher.models import EmailAlert
from watcher.models import EmailRecipient
from watcher.models import Path

database_bp = Blueprint('database', __name__)

@database_bp.cli.command('create-all')
def create_all():
    db.create_all()
