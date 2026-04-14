import argparse
import configparser
import csv
import ctypes
import io
import logging.config
import smtplib
import subprocess

from email.message import EmailMessage
from pprint import pprint

def get_uptime_seconds():
    return ctypes.windll.kernel32.GetTickCount64() / 1000

def get_tasks():
    result = subprocess.run(
        ["schtasks", "/query", "/v", "/fo", "csv"],
        capture_output=True,
        text=True,
        check=True
    )
    reader = csv.DictReader(io.StringIO(result.stdout))
    yield from reader

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args(argv)

    cp = configparser.ConfigParser()
    cp.read(args.config)

    if set(['loggers', 'handlers', 'formatters']).issubset(cp.keys()):
        logging.config.fileConfig(cp)

    logger = logging.getLogger('schtaskcheck')

    uptime_seconds = int(cp['schtasks'].get('uptime_seconds', '0'))
    if get_uptime_seconds() <= uptime_seconds:
        return

    smtp_config = dict(cp['smtp'])
    email_config = dict(cp['email_message'])

    alerts = {}
    for suffix in cp['schtasks']['alerts'].split():
        alert = dict(cp[f'alert.{suffix}'])
        assert set(alerts.keys()).issubset(['select'])
        alerts[suffix] = alert

    # Loop through all tasks checking all conditions against them, saving those
    # that fail.
    logger.info("checking scheduled tasks' conditions")
    alerts_for_tasks = []
    for task in get_tasks():
        task = {key.replace(' ', '_'): value for key, value in task.items()}
        for alert_name, alert in alerts.items():
            if eval(alert['select'], locals=task):
                if eval(alert['alert'], locals=task):
                    alerts_for_tasks.append({'alert': alert, 'task': task})

    # If any failed conditions, build and send an email.
    if alerts_for_tasks:
        logger.info("%s alerts generated", len(alerts_for_tasks))
        if len(alerts_for_tasks) > 1:
            body = ['Alerts for scheduled tasks']
        else:
            body = ['Alert for scheduled task']

        for alert_data in alerts_for_tasks:
            body.append('-' * 3)
            alert = alert_data['alert']
            task = alert_data['task']
            body.append(f'"{task["TaskName"]}" alerted for condition "{alert["alert"]}"')

        msg = EmailMessage()
        for key, value in email_config.items():
            msg[key] = value
        msg.set_content('\n'.join(body))
        with smtplib.SMTP(**smtp_config) as smtp:
            smtp.send_message(msg)
            logger.info('email sent')

if __name__ == '__main__':
    main()
