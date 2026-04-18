import uuid
import logging
import operator

from markupsafe import Markup

from watcher.extension import db

from .condition_node import ConditionNode

logger = logging.getLogger(__name__)

class ConditionGroup(ConditionNode):

    __tablename__ = 'condition_group'

    __mapper_args__ = {
        'polymorphic_identity': 'group',
    }

    id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('condition_node.id'),
        primary_key = True,
    )

    logical_operator = db.Column(
        db.String,
        nullable = False,
    )

    __logical_operators__ = set([
        'and',
        'or',
    ])

    @db.validates('logical_operator')
    def validate(self, key, value):
        if value not in self.__logical_operators__:
            raise ValueError(f'Invalid operator {value}')
        return value

    def as_string(self):
        childs = (child.as_string() for child in self.children)
        if self.logical_operator == 'and':
            separator = ' and '
        else:
            separator = ' or '
        return separator.join(childs)

    def __str__(self):
        return self.as_string()

    def as_html(self):
        childs = (child.as_html() for child in self.children)
        if self.logical_operator == 'and':
            separator = ' <span class="logic">and</span> '
        else:
            separator = ' <span class="logic">or</span> '
        return Markup(f'<span class="expr">{separator.join(childs)}</span>')

    def test_path(self, path_object, alert):
        # generator to allow short-circuit
        results = (child.test_path(path_object, alert) for child in self.children)

        if self.logical_operator == 'and':
            result = all(boolval for boolval in results)
        else:
            result = any(boolval for boolval in results)

        return result
