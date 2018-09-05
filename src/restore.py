#!/usr/bin/python3
import argparse
import config
from logger import logging as log
from openshift_client import OpenshiftClient
import os
import utils
import yaml

from kubernetes.client.rest import ApiException


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--backup-project-name', dest='backup_project_name', required=True,
                        help='The backed up project to restore')
    parser.add_argument('--restore-project-name', dest='restore_project_name', required=True,
                        help='The backed up project to restore')
    parser.add_argument('--git-backup-repo', dest='backup_repo', required=True,
                        help='The ip/hostname of the middleware proxy')
    parser.add_argument('--git-secret-repo', dest='secret_repo', required=True,
                        help='The ip/hostname of the middleware proxy')
    parser.add_argument('--openshift-token', dest='openshift_token', required=True,
                        help='Your OpenShift token. Find it here: '
                        'https://console.insights.openshift.com/console/'
                        'command-line')
    parser.add_argument('--openshift-hostname', dest='openshift_hostname', required=True,
                        help='OpenShift api hostname')
    parser.add_argument('--openshift-ca-cert', dest='openshift_ca_cert', required=True,
                        help='SSL cert for OpenShift API')
    parser.add_argument('--git-ssh-key-loc', dest='git_ssh_key_loc',
                        help='Location to your Git SSH private key used to clone the repos.')
    parser.add_argument('--working-dir', dest='working_dir', default='.',
                        help='Location for temporary files during execution.')
    args = parser.parse_args()
    return args


def restore_from_dir(openshift_client, directory, resources):
    for resource_kind in os.listdir(directory):
        print(resources)
        if resource_kind in resources:
            resource_kind_dir = directory + '/' + resource_kind
            for single_resource in os.listdir(resource_kind_dir):
                full_path = '{0}/{1}'.format(resource_kind, single_resource)
                log.info(
                    'Restoring {}'.format(full_path))
                try:
                    with open(resource_kind_dir + '/' + single_resource, 'r') as f:
                        resource_yaml = yaml.load(f)
                    openshift_client.create_resource(
                        resource_kind, resource_yaml, args.restore_project_name)
                except ApiException as err:
                    log.error('Unable to restore {0}'.format(full_path))
                    log.debug(err)


def restore_project(args):
    log.info('Restoring project: {}'.format(args.restore_project_name))

    backup_git_repo, secret_git_repo = utils.setup_git_repos(
        args.backup_repo, args.secret_repo, args.working_dir)
    backup_git_repo.checkout_branch(args.backup_project_name)
    secret_git_repo.checkout_branch(args.backup_project_name)

    openshift_client = OpenshiftClient(
        args.openshift_hostname, 443, args.openshift_token, args.openshift_ca_cert)
    restore_from_dir(openshift_client, utils.secret_dir(
        args.working_dir), 'Secret')
    restore_from_dir(openshift_client, utils.backup_dir(
        args.working_dir), config.RESOURCES_TO_BACKUP)


if __name__ == '__main__':
    args = parse_args()
    restore_project(args)
