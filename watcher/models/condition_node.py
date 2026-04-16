import uuid
import operator

from watcher.extension import db

class ConditionNode(db.Model):

    __tablename__ = 'condition_node'

    __mapper_args__ = {
        'polymorphic_on': 'node_type',
        'polymorphic_identity': 'base',
    }

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    parent_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('condition_node.id'),
        nullable = True,
        index = True,
    )

    parent = db.relationship(
        'ConditionNode',
        remote_side = 'ConditionNode.id',
        back_populates = 'children',
    )

    children = db.relationship(
        'ConditionNode',
        back_populates = 'parent',
    )

    node_type = db.Column(
        db.String,
        nullable = False,
    )
