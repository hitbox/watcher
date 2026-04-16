from flask import Blueprint
from flask import render_template

from watcher.extension import db
from watcher.html import Table
from watcher.html import unordered_list
from watcher.html import TableColumn
from watcher.models import Alert

alerts_bp = Blueprint('alerts', __name__)

def unordered_list_of_paths(paths):
    return unordered_list([path.path for path in paths])

def condition_as_string(condition):
    return condition.as_string()

alerts_table = Table(
    columns = [
        TableColumn('Name', 'name'),
        TableColumn('Description', 'description'),
        TableColumn('Paths', 'paths', cast=unordered_list_of_paths),
        TableColumn('Conditions', 'root_condition', cast=condition_as_string),
    ],
    model = Alert,
)

@alerts_bp.route('/')
def index():
    instances = db.session.scalars(db.select(Alert))
    context = {
        'table': alerts_table,
        'instances': instances,
    }
    return render_template('alerts.html', **context)
