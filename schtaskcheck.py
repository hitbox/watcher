import argparse
import configparser
import csv
import ctypes
import io
import logging.config
import re
import smtplib
import subprocess

from email.message import EmailMessage
from pprint import pprint

def get_uptime_seconds():
    """
    Host uptime in seconds.
    """
    return ctypes.windll.kernel32.GetTickCount64() / 1000

def get_tasks():
    result = subprocess.run(
        ["schtasks", "/query", "/v", "/fo", "csv"],
        capture_output=True,
        text=True,
        check=True
    )
    reader = csv.DictReader(io.StringIO(result.stdout))
    # Yield rows ignoring repeated field names.
    for row in reader:
        if set(row.values()) != set(reader.fieldnames):
            yield row

def main(argv=None):
    """
    List scheduled tasks.
    """
    parser = argparse.ArgumentParser(
        description= main.__doc__,
    )
    #parser.add_argument('config')
    parser.add_argument('output', help='CSV output filename.')
    parser.add_argument('--name', help='Regex pattern for TaskName to include')
    parser.add_argument('--status', help='Regex pattern for Status to include')
    parser.add_argument('--author')
    parser.add_argument('--ignore-name', action='append', help='Regex pattern for TaskName to ignore.')
    parser.add_argument('--ignore-status', action='append', help='Regex pattern for Status to ignore.')
    parser.add_argument('--not-disabled', action='store_true', help='Exclude Disabled tasks.')
    args = parser.parse_args(argv)

    include_disabled = not args.not_disabled

    affirm_regexes = {
        'Status': [],
        'TaskName': [],
        'Author': [],
    }

    ignore_regexes = {
        'Status': [],
        'TaskName': [],
    }

    items = [
        (args.ignore_name, 'TaskName'),
        (args.ignore_status, 'Status'),
    ]
    for option, key in items:
        if option:
            for ignore_pattern in option:
                regex = re.compile(ignore_pattern)
                ignore_regexes[key].append(regex)

    items = [
        (args.name, 'TaskName'),
        (args.status, 'Status'),
        (args.author, 'Author'),
    ]
    for option, key in items:
        if option:
            for affirm_pattern in option:
                regex = re.compile(affirm_pattern)
                affirm_regexes[key].append(regex)

    anything_pattern = '.*'
    if args.name:
        name_regex = re.compile(args.name)
    else:
        name_regex = re.compile(anything_pattern)

    if args.author:
        author_regex = re.compile(args.author)
    else:
        author_regex = re.compile(anything_pattern)

    if args.status:
        status_regex = re.compile(args.status)
    else:
        status_regex = re.compile(anything_pattern)

    matches = []
    for task in get_tasks():
        is_disabled = task['Status'] == 'Disabled'
        if args.not_disabled and is_disabled:
            continue

        # Skip if any ignore regexes match.
        skip_for_ignore = False
        for task_key, regexes in ignore_regexes.items():
            if any(regex.match(task[task_key]) for regex in regexes):
                skip_for_ignore = True
                break
        if skip_for_ignore:
            continue

        # Skip if no affirmative patterns match.
        skip_for_ignore = False
        for task_key, regexes in ignore_regexes.items():
            if any(regex.match(task[task_key]) for regex in regexes):
                skip_for_ignore = True
                break
        if skip_for_ignore:
            continue


        matches.append(task)

    if matches:
        first_task = matches[0]
        with open(args.output, 'w', newline='', encoding='utf8') as output_file:
            priortity = {'TaskName': 0, 'Comment': 1, 'Author': 2}
            fieldnames = sorted(first_task.keys(), key=lambda x: priortity.get(x, 99))
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            for task in matches:
                writer.writerow(task)

if __name__ == '__main__':
    main()
