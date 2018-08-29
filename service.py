#!/usr/bin/python3

import backup
import logger
import os
import schedule
import time

log = logger.logging


try:
    BACKUP_INTERVAL = os.environ['BACKUP_INTERVAL']
except KeyError:
    BACKUP_INTERVAL = 24


schedule.every(BACKUP_INTERVAL).hours.do(backup.full_backup)

log.info('Service started')
while True:
    schedule.run_pending()
    time.sleep(1)
