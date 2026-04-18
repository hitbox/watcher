import math
import os
import time
import uuid

from datetime import datetime

import humanize

from watcher.extension import db

class Path(db.Model):

    __tablename__ = 'path'

    id = db.Column(
        db.UUID(
            as_uuid=True, # Python side as UUID object instead of string.
        ),
        primary_key = True,
        default = uuid.uuid4,
    )

    path = db.Column(
        db.String,
        unique = True,
        nullable = False,
        index = True,
        comment = 'Filesystem path',
    )

    @db.validates('path')
    def validate_path(self, key, value):
        return os.path.normpath(value)

    alert_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey('alert.id'),
        nullable = True,
        index = True,
    )

    alert = db.relationship(
        'Alert',
        back_populates = 'paths',
    )

    __stat_attribute_mapping__ = {
        'st_mtime': 'mtime',
        'st_ctime': 'ctime',
        'st_atime': 'atime',
        'st_size': 'size',
    }

    mtime = db.Column(db.Float, nullable=True)

    ctime = db.Column(
        db.Float,
        nullable=True,
        comment = 'Creation time on Windows. Metadata change time for POSIX.',
    )

    atime = db.Column(db.Float, nullable=True)

    size = db.Column(db.BigInteger, nullable=True)

    @property
    def tail(self):
        lines = tail_lines(self.path)
        return '\n'.join(lines)

    @property
    def mtime_datetime(self):
        return datetime.fromtimestamp(self.mtime)

    @property
    def mtime_age(self):
        return time.time() - self.mtime

    @property
    def mtime_age_timedelta(self):
        """
        mtime age as datetime.timedelta
        """
        return datetime.now() - datetime.fromtimestamp(self.mtime)

    @property
    def mtime_hms(self):
        """
        mtime age as days, hours, minutes, seconds
        """
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return (days, hours, minutes, seconds)

    @property
    def mtime_human_age(self):
        """
        Human-friendly age string.
        """
        return humanize.naturaldelta(self.mtime_age_timedelta)

    @property
    def last_alert_time(self):
        return self.alert.last_time

    @property
    def normal_last_alert_time(self):
        return self.alert.normal_last_time

    @property
    def last_alert_age(self):
        if self.last_alert_time:
            return time.time() - self.last_alert_time

    @property
    def normal_last_alert_age(self):
        if self.last_alert_time is None:
            last_time = -math.inf
        else:
            last_time = self.last_alert_time
        return time.time() - last_time

    @classmethod
    def one_or_none(cls, path):
        query = db.select(cls).where(cls.path==path)
        instance = db.session.scalars(query).one_or_none()
        return instance

    def as_html(self):
        return f'<span class="path">{self.path}</span>'

    @classmethod
    def update_or_create(cls, path):
        """
        Update existing Path database object or create a new one with current
        stat info.

        Caller commits transaction.
        """
        stat_result = os.stat(path)
        query = db.select(cls).where(cls.path==path)
        instance = db.session.scalars(query).one_or_none()
        if not instance:
            instance = cls(path=path)
            db.session.add(instance)

        for stat_name, attr_name in cls.__stat_attribute_mapping__.items():
            stat_value = getattr(stat_result, stat_name)
            setattr(instance, attr_name, stat_value)

        return instance

    def update(self):
        """
        Update this object's statistics from disk.
        """
        stat_result = os.stat(self.path)
        for stat_name, attr_name in self.__stat_attribute_mapping__.items():
            stat_value = getattr(stat_result, stat_name)
            setattr(self, attr_name, stat_value)

def tail_lines(filepath, n=10, block_size=1024):
    """
    Return the last n lines of a file.
    """
    if n == 0:
        return []

    with open(filepath, 'rb') as file:
        # Seek to the end of file.
        file.seek(0, os.SEEK_END)
        data = b''
        lines = []
        remaining_size = file.tell()
        while remaining_size > 0 and len(lines) <= n:
            # Seek back a block or the remaining and read.
            read_size = min(block_size, remaining_size)
            file.seek(remaining_size - read_size, os.SEEK_SET)
            block = file.read(read_size)
            # Prepend block to data.
            data = block + data
            remaining_size -= read_size
            lines = data.splitlines()

        return [line.decode('utf-8', errors='replace') for line in lines[-n:]]
