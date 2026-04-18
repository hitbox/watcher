import logging
import smtplib
import string
import time
import uuid

from datetime import datetime
from email.message import EmailMessage

from flask import current_app

from watcher.extension import db

from .alert import Alert

logger = logging.getLogger()


class EmailTemplate(db.Model):
    """
    Default fallback values for EmailAlert unless overridden in that class.
    """

    __tablename__ = 'email_template'

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    from_address = db.Column(
        db.String,
        nullable = False,
    )

    subject_template = db.Column(
        db.String,
        nullable = False,
        comment = 'Format string with attributes from Path objects',
    )

    body_template = db.Column(
        db.Text,
        nullable = False,
        comment = 'Format string with attributes from Path objects',
    )

    is_important = db.Column(
        db.Boolean,
        nullable = False,
        comment = 'Flag to send email with the very-important header.',
    )

    email_alerts = db.relationship(
        'EmailAlert',
        back_populates = 'email_template',
    )

    recipients = db.relationship(
        'EmailRecipient',
        back_populates = 'email_template',
        cascade = 'all, delete-orphan',
    )

