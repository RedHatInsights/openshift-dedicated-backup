#!/usr/bin/python3
import logging
import os

try:
    LOG_LEVEL = os.environ['LOG_LEVEL']
except KeyError:
    LOG_LEVEL = 'WARNING'

logging.basicConfig(
    level=LOG_LEVEL, format='%(asctime)s | %(levelname)s | %(message)s')
