import logging
import operator as operator_lib
import uuid

from watcher.extension import db

from .condition_node import ConditionNode
from .path import Path

logger = logging.getLogger(__name__)

class ConditionLeaf(ConditionNode):

    __tablename__ = 'condition_leaf'

    __mapper_args__ = {
        'polymorphic_identity': 'leaf',
    }

    id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('condition_node.id'),
        primary_key = True,
    )

    field = db.Column(
        db.String,
        nullable = False,
        comment = 'Path object attribute to get value for condition',
    )

    __path_fields__ = {
        'mtime': float,
        'mtime_age': float,
        'ctime': float,
        'atime': float,
        'size': int,
        'last_alert': float,
        'last_alert_age': float,
        'normal_last_alert': float,
        'normal_last_alert_age': float,
    }

    @db.validates('field')
    def validate_field(self, key, value):
        if value not in self.__path_fields__:
            raise ValueError(f'Invalid field {value}')
        return value

    operator = db.Column(
        db.String,
        nullable = False,
        comment = 'Comparison operator name.'
    )

    __operators__ = {
        'eq': operator_lib.eq,
        'ne': operator_lib.ne,
        'lt': operator_lib.lt,
        'gt': operator_lib.gt,
        'le': operator_lib.le,
        'ge': operator_lib.ge,
    }

    @db.validates('operator')
    def validate_operator(self, name, value):
        if value not in self.__operators__:
            raise ValueError(f'Invalid operator {value!r}')
        return value

    def operator_func(self):
        return self.__operators__[self.operator]

    value = db.Column(
        db.String,
        nullable = False,
    )

    value_type = db.Column(
        db.String,
        nullable = False,
    )

    __value_types__ = {
        'str': str,
        'int': int,
        'float': float,
    }

    @db.validates('value_type')
    def validate(self, key, value):
        if value not in self.__value_types__:
            raise ValueError(f'Invalid value type {value!r}')
        return value

    def typed_value(self):
        return self.__value_types__[self.value_type](self.value)

    def as_string(self):
        operator = self.operator_func()
        condition_value = self.typed_value()
        return f'{self.operator}(Path.{self.field}, {condition_value})'

    def __str__(self):
        return self.as_string()

    def test_path(self, path, alert):
        path_field_value = getattr(path, self.field)
        operator = self.operator_func()
        condition_value = self.typed_value()
        logger.info(f'{operator}({path_field_value}, {condition_value})')
        return operator(path_field_value, condition_value)
