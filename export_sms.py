#!/usr/bin/env python3

import os
import sys
import argparse
import sqlite3
import uuid
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

# The SQL command to select which messages to retrieve
#    remoteUid : The contact's phone number
#    direction : The message direction, can be 1 (received) or 2 (sent)
#    startTime : When the message was sent (timestamp)
#    freeText  : The text of the actual message
#    isRead    : Whether the message is read (1) or not (0)
#    type      : Messages are of type 2

QUERY = """
  SELECT
    remoteUid, direction, startTime, isRead, freeText, endTime
  FROM Events
  WHERE type=2;
"""

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['xml'])
)

parser = argparse.ArgumentParser(description='Export jolla sms')
parser.add_argument('db_path', help='Path to commhistory.db')


class SMS:
    def __init__(self, result):
        self.sender = result[0]
        self.received = result[1] == 1
        self.read = result[3] == 1
        self.body = result[4]
        self.date_sent = result[2]
        self.date_received = result[5]

    def __str__(self):
        template = env.get_template('sms_item.xml')
        return template.render(sms=self)

    @property
    def sent(self):
        return not self.received


def export(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(QUERY)

    counter = 0
    results = []
    for result in cursor.fetchall():
        counter += 1
        sms = SMS(result)
        results.append(sms)
    template = env.get_template('sms.xml')
    now = datetime.now()
    xml = template.render(
        results=results, sms_count=counter, uuid=uuid.uuid4(),
        now=now, timestamp=int(now.timestamp()))
    print(xml)


if __name__ == '__main__':
    args = parser.parse_args()
    if not os.path.exists(args.db_path):
        print('File does not exist', file=sys.stderr)
        sys.exit(1)
    export(args.db_path)
