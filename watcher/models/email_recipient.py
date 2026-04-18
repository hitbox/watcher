import uuid

from watcher.extension import db

class EmailRecipient(db.Model):
    """
    Link an email address to either and EmailAlert or an EmailTemplate object's
    recipients lists.
    """

    __tablename__ = 'email_recipient'

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    address = db.Column(
        db.String,
        nullable = False,
        comment = 'Email recipient address.',
    )

    alert_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('alert.id'),
        nullable = True,
        index = True,
    )

    alert = db.relationship(
        'EmailAlert',
        back_populates = 'recipients',
    )

    email_template_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('email_template.id'),
        nullable = True,
        index = True,
    )

    email_template = db.relationship(
        'EmailTemplate',
        back_populates = 'recipients',
    )

    __table_args__ = (
        # Ensure each row belongs to exactly ONE parent:
        # - either an EmailAlert OR an EmailTemplate
        # - not both, not neither
        db.CheckConstraint(
            '(alert_id IS NOT NULL) != (email_template_id IS NOT NULL)',
            name = 'exactly_one_parent'
        ),

        # Prevent duplicate recipients on the same alert.
        # Enforce unique (address, alert_id) ONLY when alert_id is present.
        db.Index(
            'uq_alert_recipient',
            'address',
            'alert_id',
            unique = True,
            postgresql_where = db.text('alert_id IS NOT NULL'),
        ),

        # Prevent duplicate recipients on the same alert.
        # Enforce unique (address, email_template_id) ONLY when template is present.
        db.Index(
            'uq_template_recipient',
            'address',
            'email_template_id',
            unique = True,
            postgresql_where = db.text('email_template_id IS NOT NULL'),
        ),
    )

