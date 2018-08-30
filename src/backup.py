#!/usr/bin/python3

import config
import datetime
from logger import logging as log
from openshift_client import OpenshiftClient
import utils
import yaml

from kubernetes.client.rest import ApiException


def _download_resource_type_templates(project_name, resource_kind, working_dir):
    try:
        resource_names = openshift_client.get_resource_type_names(
            project_name, resource_kind)
    except ApiException as err:
        log.warn('Unable to list {0} resource in project {1}'.format(
            resource_kind, project_name))
        log.debug(err)
        return

    for name in resource_names:
        try:
            resource_file_name = '{0}/{1}/{2}.yaml'.format(
                working_dir, resource_kind, name)

            utils.create_dir('{0}/{1}'.format(working_dir, resource_kind))
            single_resource = openshift_client.get_single_resource_yaml(
                project_name, resource_kind, name)

            with open(resource_file_name, 'w') as resource_file:
                yaml.dump(single_resource.to_dict(),
                          resource_file, default_flow_style=False)
        except ApiException as err:
            log.warn('Unable to backup {0}'.format(resource_file_name))
            log.debug(err)


def _download_project_templates(project_name):
    for resource_type in config.RESOURCES_TO_BACKUP:
        _download_resource_type_templates(project_name, resource_type,
                                          args.BACKUP_GIT_WORKING_DIR)


def _download_project_secret_templates(project_name):
    _download_resource_type_templates(
        project_name, 'Secret', args.SECRET_GIT_WORKING_DIR)


def _cleanup_temp_files():
    utils.remove_dir(args.BACKUP_GIT_WORKING_DIR)
    utils.remove_dir(args.SECRET_GIT_WORKING_DIR)
    utils.remove_file(args.temp_ssh_file)
    utils.remove_file(args.temp_cert_file)


def full_backup():
    log.info('Starting full backup')
    projects = openshift_client.get_projects()

    for project in projects.items:
        name = project.metadata.name
        log.info('Backing up project: {0}'.format(name))

        commit_msg = '{0}'.format(
            name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        backup_git_repo.checkout_branch(name)
        _download_project_templates(name)
        backup_git_repo.commit_all(commit_msg)

        secret_git_repo.checkout_branch(name)
        _download_project_secret_templates(name)
        secret_git_repo.commit_all(commit_msg)

    backup_git_repo.push_all()
    secret_git_repo.push_all()
    utils.cleanup_temp_files()

    log.info('Backup complete')


args = config.parse_env()
openshift_client = OpenshiftClient(
    args.KUBERNETES_SERVICE_HOST, args.KUBERNETES_SERVICE_PORT, args.KUBERNETES_TOKEN, args.SERVICE_CERT_FILENAME)
backup_git_repo, secret_git_repo = utils.setup_git_repos(
    args.BACKUP_GIT_REPO, args.SECRET_GIT_REPO, args.WORKING_DIR, args.GIT_SSH_PRIVATE_KEY_LOC)

if __name__ == '__main__':
    try:
        full_backup()
    except KeyboardInterrupt:
        log.error('Stopping. Backup incomplete!')
        _cleanup_temp_files()
