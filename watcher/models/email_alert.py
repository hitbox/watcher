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
    )

    def render(self, template, path):
        return template.format(
            pathobj = path,
            now = datetime.now(),
            alert = self,
        )

    def do_alert(self, path_object):
        msg = EmailMessage()

        subject = self.render(self.subject_template, path_object)
        body = self.render(self.body_template, path_object)

        msg["Subject"] = subject
        msg["From"] = self.from_address

        recipients = [r.address for r in self.recipients]
        to_addresses = ', '.join(recipients)
        msg["To"] = to_addresses

        msg.set_content(body)

        smtp_host = current_app.config['SMTP_HOST']
        args = [smtp_host]
        smtp_port = current_app.config.get('SMTP_PORT')
        if smtp_port is not None:
            args.append(smtp_port)
        with smtplib.SMTP(*args) as smtp:
            smtp.send_message(msg)

        # Update last alert time.
        self.last_time = time.time()
        logger.info('Sent email subject=%r, to=%r', subject, to_addresses)
