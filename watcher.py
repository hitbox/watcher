import argparse
import os
import smtplib
import time

from configparser import ConfigParser
from configparser import ExtendedInterpolation
from email.message import EmailMessage

instance_config_path = 'instance/watcher.ini'

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


def human_split(string):
    return string.replace(',', ' ').split()

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

    config_filenames = args.config or []

    if args.instance_config:
        config_filenames.append(instance_config_path)

    cp = WatcherConfigParser()
    cp.read(config_filenames)

    # SMTP configuration.
    smtp_config = dict(cp['smtp'])

    # Test SMTP
    with smtplib.SMTP(**smtp_config) as smtp:
        pass

    # Email templates from configuration.
    emails = {key: cp['email.' + key] for key in human_split(cp['email']['keys'])}

    # Get list of all referenced watcher sections, raising for key errors.
    watcher_sections = [cp['alert.' + key] for key in human_split(cp['watcher']['alerts'])]

    # Construct all watches from configuration.
    watches = []
    for section in watcher_sections:
        func_expr = section['func']
        func = eval('lambda path: ' + func_expr)
        watch = dict(
            func_expr = func_expr,
            paths = [],
            func = func,
            email_key = section['email'],
        )
        for key, value in section.items():
            # Allow "path", "path1", "path2", etc.
            if key.startswith('path') and key[4:] == '' or key[4:].isdigit():
                watch['paths'].append(value)
        # Raise for empty paths.
        if not watch['paths']:
            raise ValueError('Empty paths.')
        watches.append(watch)

    # Test all watches for alerts.
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
                    string = template.format(path=path, **watch)
                    if key.lower() == 'body':
                        email_message.set_content(string)
                    else:
                        email_message[key] = string

                # Send email alert.
                with smtplib.SMTP(**smtp_config) as smtp:
                    smtp.send_message(email_message)

if __name__ == '__main__':
    main()
