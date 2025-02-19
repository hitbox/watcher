import argparse
import os
import smtplib
import time

from configparser import ConfigParser
from configparser import ExtendedInterpolation
from email.message import EmailMessage

instance_config_path = 'instance/watcher.ini'

keys_for_set_contents = set([
    'body',
])

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

    @property
    def age_seconds(self):
        return time.time() - os.path.getmtime(self.path)

    @property
    def age_minutes(self):
        return self.age_seconds / 60

    @property
    def age_hours(self):
        return self.age_minutes / 60

    @property
    def age_days(self):
        return self.age_hours / 24


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
    Return a list of watch data.
    """
    keys = human_split(cp['watcher']['alerts'])
    watcher_sections = [cp['alert.' + key] for key in keys]
    # Construct all watches from configuration.
    watches = []
    for section in watcher_sections:
        # Add paths from section.
        paths = []
        for key, value in section.items():
            # Allow "path", "path1", "path2", etc.
            if is_prefixed(key, 'path'):
                paths.append(value)
        # Create and append a watch.
        func_expr = section['func']
        func = eval('lambda path: ' + func_expr)
        email_key = section['email']
        watch = dict(
            func_expr = func_expr,
            paths = paths,
            func = func,
            email_key = email_key,
        )
        watches.append(watch)
    return watches

def raise_for_sanity(emails, watches):
    """
    Check the sanity of objects created from config.
    """
    # Raise for missing email keys.
    for watch in watches:
        email_key = watch['email_key']
        if email_key not in emails:
            raise KeyError(f'Invalid email key {email_key}.')

    for watch in watches:
        # Raise for empty paths.
        if not watch['paths']:
            raise ValueError('Empty paths.')
        # Raise for any path not found.
        for path in watch['paths']:
            if not os.path.exists(path):
                raise FileNotFoundError(path)

def check_and_alert(smtp_config, emails, watches):
    """
    Test each watch path against the alert expression and send emails.
    """
    for watch in watches:
        # Test each path for alert.
        for path in watch['paths']:
            path = WatcherPath(path)
            need_alert = watch['func'](path)
            if need_alert:
                # Construct email from format strings.
                email_template = emails[watch['email_key']]
                email_message = EmailMessage()
                for key, template in email_template.items():
                    # Format string.
                    subs = dict(path=path, func_expr=watch['func_expr'])
                    string = template.format(**subs)
                    if key.lower() in keys_for_set_contents:
                        email_message.set_content(string)
                    else:
                        email_message[key] = string
                # Send email alert.
                with smtplib.SMTP(**smtp_config) as smtp:
                    smtp.send_message(email_message)

def run_from_args(args):
    cp = WatcherConfigParser()
    cp.read(config_filenames_from_args(args))

    # SMTP configuration.
    smtp_config = dict(cp['smtp'])

    # Test SMTP
    with smtplib.SMTP(**smtp_config):
        pass

    # Email templates from configuration.
    emails = emails_from_config(cp)

    # Get list of all referenced watcher sections, raising for key errors.
    watches = watches_from_config(cp)

    # Raise early for sanity.
    raise_for_sanity(emails, watches)

    # Check and alert for all watches.
    check_and_alert(smtp_config, emails, watches)

def main(argv=None):
    parser = argparse.ArgumentParser()
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
