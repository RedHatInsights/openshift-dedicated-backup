#!/usr/bin/python3
from logger import logging as log
import os

try:
    WORKING_DIR = os.environ['WORKING_DIR']
except KeyError:
    WORKING_DIR = '.'

BACKUP_GIT_WORKING_DIR = WORKING_DIR + '/backup'
SECRET_GIT_WORKING_DIR = WORKING_DIR + '/secret'
temp_ssh_file = None
temp_cert_file = None

try:
    GIT_SSH_PRIVATE_KEY_LOC = os.environ['GIT_SSH_PRIVATE_KEY_LOC']
except KeyError:
    try:
        private_key = os.environ['GIT_SSH_PRIVATE_KEY']
        GIT_SSH_PRIVATE_KEY_LOC = temp_ssh_file = WORKING_DIR + '/ssh_key'
        f = open(GIT_SSH_PRIVATE_KEY_LOC, 'w')
        f.write(private_key)
        f.close()
        os.chmod(GIT_SSH_PRIVATE_KEY_LOC, 0o600)
    except KeyError:
        log.error(
            'Either GIT_SSH_PRIVATE_KEY_LOC or GIT_SSH_PRIVATEY_KEY environment variable must be set.')
        exit(1)

try:
    LOG_LEVEL = os.environ['LOG_LEVEL']
except KeyError:
    LOG_LEVEL = 'WARNING'

try:
    BACKUP_GIT_REPO = os.environ['BACKUP_GIT_REPO']
except KeyError:
    log.error('BACKUP_GIT_REPO environment variable must be set.')
    exit(1)

try:
    SECRET_GIT_REPO = os.environ['SECRET_GIT_REPO']
except KeyError:
    log.error('SECRET_GIT_REPO environment variable must be set.')
    exit(1)

try:
    KUBERNETES_SERVICE_HOST = os.environ['KUBERNETES_SERVICE_HOST']
except KeyError:
    log.error('KUBERNETES_SERVICE_HOST environment variable must be set.')
    exit(1)

try:
    KUBERNETES_SERVICE_PORT = os.environ['KUBERNETES_SERVICE_PORT']
except KeyError:
    log.error('KUBERNETES_SERVICE_PORT environment variable must be set.')
    exit(1)

try:
    KUBERNETES_TOKEN = os.environ['KUBERNETES_TOKEN']
except KeyError:
    log.error('KUBERNETES_TOKEN environment variable must be set.')
    exit(1)

try:
    SERVICE_CERT_FILENAME = os.environ['SERVICE_CERT_FILENAME']
except KeyError:
    try:
        service_cert = os.environ['SERVICE_CERT']
        SERVICE_CERT_FILENAME = temp_cert_file = WORKING_DIR + '/ca.crt'
        f = open(SERVICE_CERT_FILENAME, 'w')
        f.write(service_cert)
        f.close()
        os.chmod(SERVICE_CERT_FILENAME, 0o600)
    except KeyError:
        log.error(
            'Either SERVICE_CERT_FILENAME or SERVICE_CERT environment variable must be set.')
        exit(1)
