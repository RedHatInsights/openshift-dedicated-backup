#!/usr/bin/python3

import config
import os
from logger import logging as log

from kubernetes import client
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient


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
            config.KUBERNETES_TOKEN.strip('\n')
        if not os.path.isfile(config.SERVICE_CERT_FILENAME):
            raise ApiException("Service certification file does not exists.")
        with open(config.SERVICE_CERT_FILENAME) as f:
            if not f.read():
                raise ApiException("Cert file exists but empty.")
            configuration.ssl_ca_cert = config.SERVICE_CERT_FILENAME
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
