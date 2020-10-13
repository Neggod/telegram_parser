#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import time
import logging
from configparser import ConfigParser, MissingSectionHeaderError
from celery import Celery
from celery.schedules import crontab

from google_sheets import to_googlesheet
from kombu import Queue, Exchange


try:
    import socks
except (ImportError, ModuleNotFoundError):
    import sys
    import subprocess

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(BASE_DIR, 'requirements.txt')
    PIPE = subprocess.PIPE
    p = subprocess.Popen(sys.executable + f' -m pip3 install -r {input_file}', shell=True)
    p.wait()
    import socks
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, Channel, Message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='start_log.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg = os.path.join(BASE_DIR, 'config.ini')

parser = ConfigParser()
try:
    parser.read(cfg, encoding='UTF-8')
except MissingSectionHeaderError:
    print('Someone edit config file with fucking windows notepad!')
    temp = None
    with open(cfg, 'rb') as config:
        temp = config.read().decode("utf-8-sig").encode("utf-8")
    with open(cfg, 'wb') as config:
        config.write(temp)
    parser.read(cfg, encoding='UTF-8')

# bot values
api_id = parser.get('App_values', 'api_id')
api_hash = parser.get('App_values', 'api_hash')

client = TelegramClient('work_session', api_id, api_hash, device_model='Tesla Model S',
                        # connection=connection.ConnectionTcpMTProxyIntermediate,
                        # если есть MTProto proxy - убрать решетки над и под этой надписью, отредактировать запись снизу
                        # главное скобки не упустить.
                        # proxy=('host', 443, 'secret'))
                        )#proxy=(socks.SOCKS5, '127.0.0.1', 1088))


async def main():
    values = {}
    now = datetime.date.today()
    yesterday = now + datetime.timedelta(days=-1)
    values['date'] = yesterday.strftime("%d-%m-%Y")
    for _, query in parser['Donor_Channels'].items():
        answer = await parse_channel(query, now, yesterday)
        values.update(answer)
    to_googlesheet(values)


async def parse_channel(query, now, yesterday):
    donor: Channel = await client.get_entity(query)

    answer = {}

    async for m in client.iter_messages(donor, offset_date=now):
        if m.date.day < yesterday.day:
            print('end')
            break
        char = await client.get_entity(m.from_id)
        if char.bot:
            continue
        answer[donor.title] = answer.get(donor.title, 0) + 1
    return answer


app = Celery(__name__)
app.conf.broker_url = 'redis://localhost:6379/2'

app.conf.result_backend = 'redis://localhost:6379/2'


# app.conf.update(
#     task_queues=(
#         Queue('default', Exchange('default'), routing_key='default'),
#         Queue('for_task_2', Exchange('for_task_2'), routing_key='for_task_2'),
#     ), task_routes={
#         'test_2': {'queue': 'for_task_2', 'routing_key': 'for_task_2'},
#     }
# )


# app.control.add_consumer('high')
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute=0, hour=1), starter.s('world'))


@app.task
def starter(*args, **kwargs):
    logger.info('Task created')
    client.start()
    client.loop.run_until_complete(main())

    logger.info(f"Task complete")
    return True


if __name__ == '__main__':
    """
    Надо запускать оба:
    создаёт событие
    $celery -A main beat -l INFO
    выполняет событие
    $celery -A main worker --loglevel=INFO

    """
    client.start()
    client.loop.run_until_complete(main())
