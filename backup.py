#!/usr/bin/python3

import datetime
import logger
import os
import shutil
import yaml

from kubernetes import client
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from git import Repo
from git.exc import GitCommandError

log = logger.logging

try:
    BACKUP_GIT_WORKING_DIR = os.environ['BACKUP_GIT_WORKING_DIR']
except KeyError:
    BACKUP_GIT_WORKING_DIR = './backup'

try:
    SECRET_GIT_WORKING_DIR = os.environ['SECRET_GIT_WORKING_DIR']
except KeyError:
    SECRET_GIT_WORKING_DIR = './backup-secrets'

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
    GIT_SSH_PRIVATE_KEY_LOC = os.environ['GIT_SSH_PRIVATE_KEY_LOC']
except KeyError:
    try:
        private_key = os.environ['GIT_SSH_PRIVATE_KEY']
        GIT_SSH_PRIVATE_KEY_LOC = '/tmp/ssh_key'
        f = open(GIT_SSH_PRIVATE_KEY_LOC, 'w')
        f.write(private_key)
        f.close()
        os.chmod(GIT_SSH_PRIVATE_KEY_LOC, 0o600)
    except KeyError:
        log.error(
            'Either GIT_SSH_PRIVATE_KEY_LOC or GIT_SSH_PRIVATEY_KEY environment variable must be set.')
        exit(1)

try:
    SERVICE_CERT_FILENAME = os.environ['SERVICE_CERT_FILENAME']
except KeyError:
    try:
        service_cert = os.environ['SERVICE_CERT']
        SERVICE_CERT_FILENAME = '/tmp/ca.crt'
        f = open(SERVICE_CERT_FILENAME, 'w')
        f.write(service_cert)
        f.close()
        os.chmod(SERVICE_CERT_FILENAME, 0o600)
    except KeyError:
        log.error(
            'Either SERVICE_CERT_FILENAME or SERVICE_CERT environment variable must be set.')
        exit(1)


class GitRepo(object):
    def __init__(self, remote, working_dir):
        log.info('Cloning git repo: {0} into: {1}'.format(remote, working_dir))
        self.remote = remote
        self.working_dir = working_dir

        ssh_cmd = 'ssh -i {0}'.format(GIT_SSH_PRIVATE_KEY_LOC)
        self.repo = Repo.init(working_dir)
        self.repo.git.update_environment(GIT_SSH_COMMAND=ssh_cmd)

        self.origin = self.repo.create_remote('origin', self.remote)
        self.origin.fetch()
        self.repo.create_head('master', self.origin.refs.master).set_tracking_branch(
            self.origin.refs.master).checkout()

    def checkout_branch(self, branch_name):
        try:
            self.repo.create_head(branch_name, self.origin.refs[branch_name]).set_tracking_branch(
                self.origin.refs[branch_name]).checkout()
            self.repo.heads[branch_name].checkout()
        except (GitCommandError, IndexError, AttributeError):
            self.repo.git.checkout('-b', branch_name)
            self.repo.git.reset('--hard', 'origin/master')

    def commit_all(self, msg):
        try:
            self.repo.git.add('.')
            self.repo.git.commit('-m', msg)
        except GitCommandError:
            pass  # nothing to commit

    def push_all(self):
        self.repo.git.push('--all', 'origin')


class OpenshiftClient(object):
    def __init__(self):
        self.client = self.connect()

    def connect(self):
        kubernetes_host = "https://%s:%s" % (
            os.getenv("KUBERNETES_SERVICE_HOST"), os.getenv("KUBERNETES_SERVICE_PORT"))
        log.info('Connecting to OpenShift {0}'.format(kubernetes_host))

        configuration = client.Configuration()
        configuration.host = kubernetes_host
        configuration.api_key['authorization'] = "bearer " + \
            KUBERNETES_TOKEN.strip('\n')
        if not os.path.isfile(SERVICE_CERT_FILENAME):
            raise ApiException("Service certification file does not exists.")
        with open(SERVICE_CERT_FILENAME) as f:
            if not f.read():
                raise ApiException("Cert file exists but empty.")
            configuration.ssl_ca_cert = SERVICE_CERT_FILENAME
        client.Configuration.set_default(configuration)
        k8s_client = client.api_client.ApiClient()
        return DynamicClient(k8s_client)

    def get_projects(self):
        projects = self.client.resources.get(
            api_version='project.openshift.io/v1', kind='Project')
        return projects.get()

    def get_resource_type_names(self, project_name, resource_kind):
        resource = self.client.resources.get(
            api_version='v1', kind=resource_kind)
        resource_list = resource.get(namespace=project_name)
        names = []
        resource_dict = resource_list.to_dict()
        for item in resource_dict['items']:
            names.append(item['metadata']['name'])
        return names

    def get_single_resource_yaml(self, project_name, resource_kind, resource_name):
        resource = self.client.resources.get(
            api_version='v1', kind=resource_kind)
        resource_yaml = resource.get(
            name=resource_name, namespace=project_name, query_params=[('exact', 'false'), ('export', 'true')])
        return resource_yaml


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

            _create_dir('{0}/{1}'.format(working_dir, resource_kind))
            single_resource = openshift_client.get_single_resource_yaml(
                project_name, resource_kind, name)

            with open(resource_file_name, 'w') as resource_file:
                yaml.dump(single_resource.to_dict(),
                          resource_file, default_flow_style=False)
        except ApiException as err:
            log.warn('Unable to backup {0}'.format(resource_file_name))
            log.debug(err)


def _download_project_templates(project_name):
    types_to_backup = ['Service',
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
    for resource_type in types_to_backup:
        _download_resource_type_templates(project_name, resource_type,
                                          BACKUP_GIT_WORKING_DIR)


def _download_project_secret_templates(project_name):
    _download_resource_type_templates(
        project_name, 'Secret', SECRET_GIT_WORKING_DIR)


def _create_dir(project_name):
    try:
        os.makedirs(project_name)
    except OSError:
        log.debug('{0} directory already exists.'.format(project_name))


def _remove_dir(directory):
    try:
        os.listdir(directory)
        shutil.rmtree(directory)
    except FileNotFoundError:
        pass


def _setup_git_repo(repo, working_dir):
    _remove_dir(working_dir)
    git_repo = GitRepo(
        repo, working_dir)
    return git_repo


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

    _remove_dir(BACKUP_GIT_WORKING_DIR)
    _remove_dir(SECRET_GIT_WORKING_DIR)

    log.info('Backup complete')


openshift_client = OpenshiftClient()
backup_git_repo = _setup_git_repo(BACKUP_GIT_REPO, BACKUP_GIT_WORKING_DIR)
secret_git_repo = _setup_git_repo(SECRET_GIT_REPO, SECRET_GIT_WORKING_DIR)

if __name__ == '__main__':
    full_backup()
