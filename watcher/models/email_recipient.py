import uuid

from watcher.extension import db

class EmailRecipient(db.Model):

    __tablename__ = 'email_recipient'

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    address = db.Column(
        db.String,
        nullable = False,
        unique = True,
        comment = 'Email recipient address.',
    )

    alert_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('alert.id'),
        nullable = False,
        index = True,
    )

    alert = db.relationship(
        'EmailAlert',
        back_populates = 'recipients',
    )
