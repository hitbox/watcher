import argparse
import logging.config
import os
import pickle
import smtplib
import time
import unittest

from collections import namedtuple
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from email.message import EmailMessage

instance_config_path = 'instance/watcher.ini'

keys_for_set_contents = set([
    'body',
])

class TestWatcherArchive(unittest.TestCase):

    def test_no_last(self):
        archive = WatcherArchive({}, 'test_watch_name', '/fake/path/to/archive')
        self.assertEqual(archive.last_alert_time, 0)

    def test_last_alert_time(self):
        name = 'test_watch_name'
        path = '/fake/path/to/archive'
        key = (name, path)
        archive = WatcherArchive({key: 1}, name, path)
        self.assertEqual(archive.last_alert_time, 1)


class TestMisc(unittest.TestCase):

    def test_human_split(self):
        self.assertEqual(human_split(''), [])
        self.assertEqual(human_split('alert_name'), ['alert_name'])
        self.assertEqual(human_split('alert1 alert2'), ['alert1', 'alert2'])
        self.assertEqual(human_split('alert1, alert2'), ['alert1', 'alert2'])

    def test_is_prefixed(self):
        self.assertTrue(is_prefixed('path', 'path'))
        self.assertTrue(is_prefixed('path1', 'path'))


class WatcherConfigParser(ConfigParser):
    """
    ConfigParser with ExtendedInterpolation.
    """

    def __init__(self, **kwargs):
        # ConfigParser __init__ are all keyword arguments.
        kwargs.setdefault('interpolation', ExtendedInterpolation())
        super().__init__(**kwargs)


class WatcherPath:
    """
    Wrap a path in a useful object for the alert functions to use.
    """

    def __init__(self, path):
        self.path = path
        self.stat = os.stat(self.path)

    @property
    def age_seconds(self):
        return time.time() - self.stat.st_mtime

    @property
    def age_minutes(self):
        return self.age_seconds / 60

    @property
    def age_hours(self):
        return self.age_minutes / 60

    @property
    def age_days(self):
        return self.age_hours / 24


WatcherArchiveBase = namedtuple(
    'WatcherArchiveBase',
    ['archive', 'watch_name', 'path'],
)

class WatcherArchive(WatcherArchiveBase):

    @property
    def last_alert_time(self):
        key = (self.watch_name, self.path)
        if key in self.archive:
            return self.archive[key]
        else:
            return 0

    @property
    def last_alert_age_seconds(self):
        return time.time() - self.last_alert_time

    @property
    def last_alert_age_minutes(self):
        return self.last_alert_age_seconds / 60

    @property
    def last_alert_age_hours(self):
        return self.last_alert_age_minutes / 60

    @property
    def last_alert_age_days(self):
        return self.last_alert_age_hours / 24


def config_filenames_from_args(args):
    config_filenames = args.config or []
    if args.instance_config:
        config_filenames.append(instance_config_path)
    return config_filenames

def human_split(string):
    return string.replace(',', ' ').split()

def is_prefixed(key, prefix):
    n = len(prefix)
    return key.startswith(prefix) and key[n:] == '' or key[n:].isdigit()

def emails_from_config(cp):
    """
    Return dict of keyed email templates.
    """
    keys = human_split(cp['email']['keys'])
    emails = {key: cp['email.' + key] for key in keys}
    return emails

def watches_from_config(cp):
    """
    Return dict of named watches.
    """
    watches = {}
    for watch_name in human_split(cp['watcher']['alerts']):
        # Raise for duplicate keys in string list.
        if watch_name in watches:
            raise KeyError(f'Duplicate key {watch_name}')
        section = cp['alert.' + watch_name]
        # Add paths from section.
        paths = []
        for key, value in section.items():
            # Allow "path", "path1", "path2", etc.
            if is_prefixed(key, 'path'):
                paths.append(value)
        # Create and append a watch.
        func_expr = section['func']
        email_key = section['email']
        watches[watch_name] = dict(
            func_expr = func_expr,
            paths = paths,
            email_key = email_key,
        )
    return watches

def raise_for_sanity(emails, watches):
    """
    Check the sanity of objects created from config.
    """
    # Raise for missing email keys.
    for watch in watches.values():
        email_key = watch['email_key']
        if email_key not in emails:
            raise KeyError(f'Invalid email key {email_key}.')

    for watch in watches.values():
        # Raise for empty paths.
        if not watch['paths']:
            raise ValueError('Empty paths.')
        # Raise for any path not found.
        for path in watch['paths']:
            if not os.path.exists(path):
                raise FileNotFoundError(path)

def update_last_alert(watch_name, path, archive):
    """
    Save the last alerted time by the alert's name from config and the path it
    alerted for.
    """
    archive[(watch_name, path)] = time.time()

def make_email(email_template, substitutions):
    """
    :param email_template:
        Dict of email header keys and format string values.
    """
    email_message = EmailMessage()
    for key, template in email_template.items():
        # Format string.
        string = template.format(**substitutions)
        # Update email message.
        if key.lower() in keys_for_set_contents:
            email_message.set_content(string)
        else:
            email_message[key] = string
    return email_message

def check_and_alert(smtp_config, emails, watches, archive):
    """
    Test each watch path against the alert expression and send emails.
    """
    logger = logging.getLogger('watcher')
    for watch_name, watch in watches.items():
        # Test each path for alert.
        for path in watch['paths']:
            watcher_path = WatcherPath(path)
            context = dict(
                path = watcher_path,
                archive = WatcherArchive(archive, watch_name, path),
            )
            try:
                need_alert = eval(watch['func_expr'], {}, context)
            except:
                # Log exception and continue to next path.
                logger.exception(
                    'Exception evaluating alert func for %r.', watch_name)
                continue
            if need_alert:
                # Construct email from format strings.
                email_template = emails[watch['email_key']]
                substitutions = dict(
                    path = watcher_path,
                    func_expr = watch['func_expr'],
                )
                email_message = make_email(email_template, substitutions)
                # Send email alert.
                with smtplib.SMTP(**smtp_config) as smtp:
                    smtp.send_message(email_message)
                # Update archive last alert time.
                update_last_alert(watch_name, path, archive)
                logger.info('alerted for %r', watch_name)

def load_archive(archive_path):
    if os.path.exists(archive_path) and os.path.getsize(archive_path) > 0:
        with open(archive_path, 'rb') as archive_file:
            archive = pickle.load(archive_file)
    else:
        archive = {}
    return archive

def save_archive(archive_path, archive):
    with open(archive_path, 'wb') as archive_file:
        pickle.dump(archive, archive_file)

def has_logging(cp):
    return set(['loggers', 'handlers', 'formatters']).issubset(cp)

def ensure_logging(cp):
    if has_logging(cp):
        logging.config.fileConfig(cp)
    else:
        logging.basicConfig()

def run_from_args(args):
    """
    Run configured alerts.
    """
    cp = WatcherConfigParser()
    cp.read(config_filenames_from_args(args))

    # Ensure logging is configured somehow.
    ensure_logging(cp)

    # SMTP configuration.
    smtp_config = dict(cp['smtp'])

    # Email templates from configuration.
    emails = emails_from_config(cp)

    # Get list of all referenced watcher sections, raising for key errors.
    watches = watches_from_config(cp)

    # Raise early for sanity.
    raise_for_sanity(emails, watches)

    # Load archive
    archive_path = cp['watcher']['archive']
    archive = load_archive(archive_path)

    # Check and alert for all watches. Archive is updated here.
    check_and_alert(smtp_config, emails, watches, archive)

    # Save archive
    save_archive(archive_path, archive)

def main(argv=None):
    """
    Parse command line arguments and begin run.
    """
    # TODO
    # - tests for this
    # - commit and push this
    # - get on crewbrief UserEvents.txt
    parser = argparse.ArgumentParser(
        description = 'Alerts from configured expressions for files.',
    )
    parser.add_argument(
        '--config',
        nargs = '*',
        help = 'Path(s) to config files.',
    )
    parser.add_argument(
        '--instance-config',
        action = 'store_true',
        help = f'Look for config in {instance_config_path}',
    )
    args = parser.parse_args(argv)
    run_from_args(args)

if __name__ == '__main__':
    main()
