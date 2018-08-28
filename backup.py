#!/usr/bin/python3

import datetime
import logging
import os
import shutil
import yaml

from kubernetes import client
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient
from git import Repo
from git.exc import GitCommandError

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
    logging.error('BACKUP_GIT_REPO environment variable must be set.')
    exit(1)

try:
    SECRET_GIT_REPO = os.environ['SECRET_GIT_REPO']
except KeyError:
    logging.error('SECRET_GIT_REPO environment variable must be set.')
    exit(1)

try:
    KUBERNETES_SERVICE_HOST = os.environ['KUBERNETES_SERVICE_HOST']
except KeyError:
    logging.error('KUBERNETES_SERVICE_HOST environment variable must be set.')
    exit(1)

try:
    KUBERNETES_SERVICE_PORT = os.environ['KUBERNETES_SERVICE_PORT']
except KeyError:
    logging.error('KUBERNETES_SERVICE_PORT environment variable must be set.')
    exit(1)

try:
    KUBERNETES_TOKEN = os.environ['KUBERNETES_TOKEN']
except KeyError:
    logging.error('KUBERNETES_TOKEN environment variable must be set.')
    exit(1)

try:
    GIT_SSH_PRIVATE_KEY_LOC = os.environ['GIT_SSH_PRIVATE_KEY_LOC']
except KeyError:
    logging.error('GIT_SSH_PRIVATE_KEY_LOC environment variable must be set.')
    exit(1)

try:
    SERVICE_CERT_FILENAME = os.environ['SERVICE_CERT_FILENAME']
except KeyError:
    logging.error('SERVICE_CERT_FILENAME environment variable must be set.')


class GitRepo(object):
    def __init__(self, remote, working_dir):
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
        KUBERNETES_HOST = "https://%s:%s" % (
            os.getenv("KUBERNETES_SERVICE_HOST"), os.getenv("KUBERNETES_SERVICE_PORT"))

        configuration = client.Configuration()
        configuration.host = KUBERNETES_HOST
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


def download_resource_type_templates(project_name, resource_kind, working_dir):
    try:
        resource_names = openshift_client.get_resource_type_names(
            project_name, resource_kind)
    except ApiException:
        logging.warn('Unable to list {0} resource in project {1}'.format(
            resource_kind, project_name))
        return

    for name in resource_names:
        try:
            resource_file_name = '{0}/{1}/{2}.yaml'.format(
                working_dir, resource_kind, name)

            create_dir('{0}/{1}'.format(working_dir, resource_kind))
            single_resource = openshift_client.get_single_resource_yaml(
                project_name, resource_kind, name)

            with open(resource_file_name, 'w') as resource_file:
                yaml.dump(single_resource.to_dict(),
                          resource_file, default_flow_style=False)
        except ApiException:
            logging.warn('Unable to backup {0}'.format(resource_file_name))


def download_project_templates(project_name):
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
        download_resource_type_templates(project_name, resource_type,
                                         BACKUP_GIT_WORKING_DIR)


def download_project_secret_templates(project_name):
    download_resource_type_templates(
        project_name, 'Secret', SECRET_GIT_WORKING_DIR)


def create_dir(project_name):
    try:
        os.makedirs(project_name)
    except OSError:
        logging.debug('{0} directory already exists.'.format(project_name))


def remove_dir(directory):
    try:
        os.listdir(directory)
        shutil.rmtree(directory)
    except FileNotFoundError:
        pass


def setup_git_repo(repo, working_dir):
    remove_dir(working_dir)
    git_repo = GitRepo(
        repo, working_dir)
    return git_repo


openshift_client = OpenshiftClient()
backup_git_repo = setup_git_repo(BACKUP_GIT_REPO, BACKUP_GIT_WORKING_DIR)
secret_git_repo = setup_git_repo(SECRET_GIT_REPO, SECRET_GIT_WORKING_DIR)

if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)

    projects = openshift_client.get_projects()

    for project in projects.items:
        name = project.metadata.name

        commit_msg = '{1}'.format(
            name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        backup_git_repo.checkout_branch(name)
        download_project_templates(name)
        backup_git_repo.commit_all(commit_msg)

        secret_git_repo.checkout_branch(name)
        download_project_secret_templates(name)
        secret_git_repo.commit_all(commit_msg)

    backup_git_repo.push_all()
    secret_git_repo.push_all()

    remove_dir(BACKUP_GIT_WORKING_DIR)
    remove_dir(SECRET_GIT_WORKING_DIR)
