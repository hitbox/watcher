from flask import render_template
from flask.views import View

from watcher.extension import db

class TableListView(View):

    methods = ['GET', 'POST']

    def __init__(
        self,
        table,
        query = None,
        form = None,
        template = 'alerts.html',
    ):
        """
        """
        self.table = table
        self.query = query
        self.form = form
        self.template = template

    def get_form(self):
        if self.form:
            return self.form()

    def get_query(self):
        if callable(self.query):
            return self.query()
        else:
            return self.query

    def get_table(self):
        if callable(self.table):
            return self.table()
        else:
            return self.table

    def dispatch_request(self):
        form = self.get_form()

        query = self.get_query()
    
        table = self.get_table()

        if (
            form is not None
            and
            query is not None
            and
            form.validate_on_submit()
        ):
            criteria = form.get_criteria()
            query = query.where(*criteria)

        instances = db.session.scalars(query).all()

        context = {
            'form': form,
            'instances': instances,
            'table': table,
        }

        return render_template(self.template, **context)


class EditInstanceView(View):

    def __init__(
        self,
        get_instance,
        form_class,
        template = 'alerts.html',
    ):
        """
        """
        self.get_instance = get_instance
        self.form_class = form_class
        self.template = template

    def dispatch_request(self, **identity):
        instance = self.get_instance(identity)

        form = self.form_class(obj=instance)

        context = {
            'form': form,
            'instance': instance,
        }

        return render_template(self.template, **context)
