#!/usr/bin/python3
from logger import logging as log
import os
from types import SimpleNamespace

RESOURCES_TO_BACKUP = ['Service',
                       'DeploymentConfig',
                       'BuildConfig',
                       'ImageStream',
                       'Route',
                       'ConfigMap',
                       'StatefulSet',
                       # 'ProvisionedService',
                       # 'Pipeline',
                       # 'Quota',
                       # 'Pod'
                       ]


def parse_env():
    args = SimpleNamespace(**{})
    try:
        args.WORKING_DIR = os.environ['WORKING_DIR']
    except KeyError:
        args.WORKING_DIR = '.'

    args.BACKUP_GIT_WORKING_DIR = args.WORKING_DIR + '/backup'
    args.SECRET_GIT_WORKING_DIR = args.WORKING_DIR + '/secret'
    args.temp_ssh_file = None
    args.temp_cert_file = None

    try:
        args.GIT_SSH_PRIVATE_KEY_LOC = os.environ['GIT_SSH_PRIVATE_KEY_LOC']
    except KeyError:
        try:
            private_key = os.environ['GIT_SSH_PRIVATE_KEY']
            args.GIT_SSH_PRIVATE_KEY_LOC = args.temp_ssh_file = args.WORKING_DIR + '/ssh_key'
            f = open(args.GIT_SSH_PRIVATE_KEY_LOC, 'w')
            f.write(private_key)
            f.close()
            os.chmod(args.GIT_SSH_PRIVATE_KEY_LOC, 0o600)
        except KeyError:
            log.error(
                'Either GIT_SSH_PRIVATE_KEY_LOC or GIT_SSH_PRIVATEY_KEY environment variable must be set.')
            exit(1)

    try:
        args.LOG_LEVEL = os.environ['LOG_LEVEL']
    except KeyError:
        args.LOG_LEVEL = 'WARNING'

    try:
        args.BACKUP_GIT_REPO = os.environ['BACKUP_GIT_REPO']
    except KeyError:
        log.error('BACKUP_GIT_REPO environment variable must be set.')
        exit(1)

    try:
        args.SECRET_GIT_REPO = os.environ['SECRET_GIT_REPO']
    except KeyError:
        log.error('SECRET_GIT_REPO environment variable must be set.')
        exit(1)

    try:
        args.KUBERNETES_SERVICE_HOST = os.environ['KUBERNETES_SERVICE_HOST']
    except KeyError:
        log.error('KUBERNETES_SERVICE_HOST environment variable must be set.')
        exit(1)

    try:
        args.KUBERNETES_SERVICE_PORT = os.environ['KUBERNETES_SERVICE_PORT']
    except KeyError:
        log.error('KUBERNETES_SERVICE_PORT environment variable must be set.')
        exit(1)

    try:
        args.KUBERNETES_TOKEN = os.environ['KUBERNETES_TOKEN']
    except KeyError:
        log.error('KUBERNETES_TOKEN environment variable must be set.')
        exit(1)

    try:
        args.SERVICE_CERT_FILENAME = os.environ['SERVICE_CERT_FILENAME']
    except KeyError:
        try:
            service_cert = os.environ['SERVICE_CERT']
            args.SERVICE_CERT_FILENAME = args.temp_cert_file = args.WORKING_DIR + '/ca.crt'
            f = open(args.SERVICE_CERT_FILENAME, 'w')
            f.write(service_cert)
            f.close()
            os.chmod(args.SERVICE_CERT_FILENAME, 0o600)
        except KeyError:
            log.error(
                'Either SERVICE_CERT_FILENAME or SERVICE_CERT environment variable must be set.')
            exit(1)

    return args
