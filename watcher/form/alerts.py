from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField

from watcher.models import Alert

from .field import DisplayField

class AlertTableFilterForm(FlaskForm):

    is_active = SelectField(
        'Active?',
        choices = [
            ('', 'All'),
            ('only-active', 'Only Active'),
            ('only-not-active', 'Only NOT Active'),
        ],
    )

    select = SubmitField()

    def get_criteria(self):
        criteria = []
        if self.is_active.data == 'only-active':
            criteria.append(Alert.active == True)
        elif self.is_active.data == 'only-not-active':
            criteria.append(Alert.active == False)
        return criteria


class EditAlertForm(FlaskForm):

    active = BooleanField()

    type = DisplayField()

    name = StringField()

    description = StringField()

    last_time = DisplayField()


class EditEmailAlertForm(EditAlertForm):

    from_address = StringField()

    subject_template = StringField()

    body_template = StringField()

    is_important = BooleanField()

    update = SubmitField()
