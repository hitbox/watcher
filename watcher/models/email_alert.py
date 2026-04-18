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

logger = logging.getLogger(__name__)

class EmailAlert(Alert):

    __tablename__ = 'email_alert'

    __mapper_args__ = {
        'polymorphic_identity': 'email_alert',
    }

    id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('alert.id'),
        primary_key = True,
    )

    from_address = db.Column(
        db.String,
        nullable = True,
    )

    subject_template = db.Column(
        db.String,
        nullable = True,
        comment =
            'Format string with attributes from Path objects. Fallback to'
            ' email_template for None',
    )

    body_template = db.Column(
        db.Text,
        nullable = True,
        comment =
            'Format string with attributes from Path objects. Fallback to'
            ' email_template for None.',
    )

    is_important = db.Column(
        db.Boolean,
        nullable = True,
        comment =
            'Flag to send email with the very-important header. Fallback to'
            ' email_template for None.',
    )

    email_template_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('email_template.id')
    )

    email_template = db.relationship(
        'EmailTemplate',
        back_populates = 'email_alerts',
    )

    __valid_names__ = {
        'pathobj': set([
            'path',
            'alert',
            'mtime',
            'mtime_age',
            'ctime',
            'atime',
            'size',
            'tail',
        ]),
        'now': None,
        'alert': set([
            'type',
            'name',
            'description',
            'last_time',
            'normal_last_time',
            'paths',
            'root_condition',
        ]),
    }

    @db.validates('subject_template', 'body_template')
    def validate_template_fields(self, key, format_string):
        formatter = string.Formatter()

        parsed = formatter.parse(format_string)
        for literal, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue

            parts = field_name.split('.')
            if parts[0] not in self.__valid_names__:
                raise ValueError(
                    f'Invalid field name for object {parts[0]}'
                    f' in format string {format_string}')
            if len(parts[1:]) > 1:
                raise ValueError(
                    f'Format string {key}: deep attribute access'
                    f' not supported {parts[0]}.{parts[1:]}')
            elif len(parts[1:]) == 1:
                valid_attributes = self.__valid_names__[parts[0]]
                if valid_attributes is not None:
                    if parts[1] not in valid_attributes:
                        raise ValueError(
                            f'Invalid attribute {parts[1]} for {parts[0]}')

        return format_string

    recipients = db.relationship(
        'EmailRecipient',
        back_populates = 'alert',
        cascade = 'all, delete-orphan',
    )

    def render(self, template, path):
        context = {
            'pathobj': path,
            'now': datetime.now(),
            'alert': self,
        }
        return template.format(**context)

    def do_alert(self, path_object):
        msg = EmailMessage()

        subject_template = self.subject_template or self.email_template.subject_template
        body_template = self.body_template or self.email_template.body_template

        subject = self.render(subject_template, path_object)
        body = self.render(body_template, path_object)

        msg["Subject"] = subject
        msg["From"] = self.from_address or self.email_template.from_address

        if self.recipients:
            recipients = [r.address for r in self.recipients]
        elif self.email_template.recipients:
            recipients = [r.address for r in self.email_template.recipients]

        to_addresses = ', '.join(recipients)
        msg["To"] = to_addresses

        msg.set_content(body)

        smtp_host = current_app.config['SMTP_HOST']
        args = [smtp_host]
        smtp_port = current_app.config.get('SMTP_PORT')
        if smtp_port is not None:
            args.append(smtp_port)
        logger.info('SMTP args=%s', args)
        with smtplib.SMTP(*args) as smtp:
            smtp.send_message(msg)

        # Update last alert time.
        self.last_time = time.time()
        logger.info('Sent email subject=%r, to=%r, from=%s', subject, to_addresses, msg['From'])
