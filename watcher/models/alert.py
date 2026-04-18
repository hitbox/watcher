import os
import logging
import math
import uuid

from watcher.extension import db

logger = logging.getLogger(__name__)

class Alert(db.Model):

    __tablename__ = 'alert'

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'alert',
    }

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    active = db.Column(
        db.Boolean,
        nullable = False,
        default = True,
    )

    type = db.Column(
        db.String,
        nullable = False,
    )

    name = db.Column(
        db.String,
        nullable = False,
        unique = True,
        comment = 'Friendly, unique name for alert',
    )

    description = db.Column(
        db.String,
        nullable = True,
    )

    last_time = db.Column(
        db.Float,
        nullable = True,
        comment = 'Last time this alert was fired.'
    )

    @property
    def normal_last_time(self):
        """
        Normalized last alert time such that None appears as infinity ago.
        """
        if self.last_time is None:
            return -math.inf
        return self.last_time

    paths = db.relationship(
        'Path',
        back_populates = 'alert',
    )

    root_condition_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('condition_node.id'),
        nullable = False,
        index = True,
    )

    root_condition = db.relationship(
        'ConditionNode',
    )

    def alerts_for_paths(self, ignore_missing=False):
        alerts = []
        for path_object in self.paths:
            if ignore_missing and not os.path.exists(path_object.path):
                continue
            path_object.update()
            logger.info('Updated %s', path_object.path)
            if self.root_condition.test_path(path_object, self):
                alerts.append((self, path_object))
        return alerts

    def do_alert(self, path_object):
        raise NotImplementedError('No real work for a generic base-class alert.')
