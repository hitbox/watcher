from flask import Blueprint
from flask import abort
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from watcher.extension import db
from watcher.form import AlertTableFilterForm
from watcher.form import EditAlertForm
from watcher.form import EditEmailAlertForm
from watcher.html import Table
from watcher.html import TableColumn
from watcher.html import unordered_list
from watcher.models import Alert
from watcher.models import EmailAlert

from .pluggable import EditInstanceView
from .pluggable import TableListView

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')

def unordered_list_of_paths(paths):
    return unordered_list([path.as_html() for path in paths])

def condition_as_html(condition):
    return condition.as_html()

alerts_table = Table(
    columns = [
        TableColumn('Active?', 'active_yn'),
        TableColumn('Type', 'type'),
        TableColumn('Name', 'name'),
        TableColumn('Description', 'description'),
        TableColumn('Paths', 'paths', cast=unordered_list_of_paths),
        TableColumn('Conditions', 'root_condition', cast=condition_as_html),
    ],
    model = Alert,
)

@alerts_bp.route('/', methods=['GET', 'POST'])
def delete_me_list():
    """
    Table listing Alert objects.
    """
    form = AlertTableFilterForm()

    query = db.select(Alert)

    if form.validate_on_submit():
        if form.is_active.data:
            if form.is_active.data == 'only-active':
                query = query.where(Alert.active == True)
            elif form.is_active.data == 'only-not-active':
                query = query.where(Alert.active == False)

    instances = db.session.scalars(query)
    context = {
        'table': alerts_table,
        'instances': instances,
        'form': form,
    }
    return render_template('alerts.html', **context)

alerts_bp.add_url_rule(
    rule = '/list',
    view_func = TableListView.as_view(
        name = 'list',
        table = alerts_table,
        query = db.select(Alert),
        form = AlertTableFilterForm,
    ),
)

form_by_model = {
    EmailAlert: EditEmailAlertForm,
}

alerts_bp.add_url_rule(
    rule = '/edit/<uuid:id>',
    view_func = EditInstanceView.as_view(
        name = 'edit',
        form_class = EditAlertForm,
        get_instance = lambda ident: db.session.get(Alert, ident),
        template = 'edit.html',
    ),
)

@alerts_bp.route('/edit/<uuid:id>', methods=['GET', 'POST'])
def delete_me_edit(id):
    alert = db.session.get(Alert, {'id': id})
    if alert is None:
        abort(404)

    for model_class, form_class in form_by_model.items():
        if isinstance(alert, model_class):
            break
    else:
        raise TypeError(f'No form class for {type(alert)}')

    form = form_class(obj=alert)

    if form.validate_on_submit():
        form.populate_obj(alert)
        db.session.commit()
        return redirect(url_for(request.endpoint, id=id))

    context = {
        'form': form,
    }

    return render_template('edit_alert.html', **context)
