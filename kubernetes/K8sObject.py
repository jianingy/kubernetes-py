#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is subject to the terms and conditions defined in
# file 'LICENSE.md', which is part of this source code package.
#

from kubernetes.K8sConfig import K8sConfig
from kubernetes.K8sExceptions import *
from kubernetes.models.v1.BaseUrls import BaseUrls
from kubernetes.models.v1.DeleteOptions import DeleteOptions
from kubernetes.models.v1.BaseModel import BaseModel
from kubernetes.models.v1.Pod import Pod
from kubernetes.models.v1.ReplicationController import ReplicationController
from kubernetes.models.v1.Secret import Secret
from kubernetes.models.v1.Service import Service
from kubernetes.utils import HttpRequest, is_valid_dict, str_to_class

VALID_K8s_OBJS = [
    'Deployment',
    'PersistentVolume',
    'Pod',
    'ReplicaSet',
    'ReplicationController',
    'Secret',
    'Service',
    'Volume'
]


class K8sObject(object):
    def __init__(self, config=None, obj_type=None, name=None):
        super(K8sObject, self).__init__()

        if config is not None and not isinstance(config, K8sConfig):
            raise SyntaxError('K8sObject: config: [ {0} ] must be of type K8sConfig.'.format(config.__class__.__name__))
        if config is None:
            config = K8sConfig()
        self.config = config

        if obj_type not in VALID_K8s_OBJS:
            valid = ", ".join(VALID_K8s_OBJS)
            raise SyntaxError('K8sObject: obj_type: [ {0} ] must be in: [ {1} ]'.format(obj_type, valid))
        self.obj_type = obj_type

        self.model = str_to_class(obj_type)
        self.name = name

        try:
            urls = BaseUrls(api_version=self.config.version, namespace=self.config.namespace)
            self.base_url = urls.get_base_url(object_type=obj_type)
        except:
            raise Exception('Could not set BaseUrl for type: [ {0} ]'.format(obj_type))

    def __str__(self):
        return "{}".format(self.model.serialize())

    def __eq__(self, other):
        # see https://github.com/kubernetes/kubernetes/blob/release-1.3/docs/design/identifiers.md
        if isinstance(other, self.__class__):
            return self.config.namespace == other.config.namespace and self.name == other.name
        return NotImplemented

    # ------------------------------------------------------------------------------------- name

    @property
    def name(self):
        return self.model.metadata.name

    @name.setter
    def name(self, name=None):
        self.model.metadata.name = name

    # ------------------------------------------------------------------------------------- serialize

    def serialize(self):
        if self.model is None:
            return {}
        return self.model.serialize()

    def as_json(self):
        if self.model is None:
            return ""
        return ""

    def as_yaml(self):
        if self.model is None:
            return ""
        return ""

    # ------------------------------------------------------------------------------------- remote API calls

    def request(self, method='GET', host=None, url=None, auth=None, cert=None,
                data=None, token=None, ca_cert=None, ca_cert_data=None):

        host = self.config.api_host if host is None else host
        url = self.base_url if url is None else url
        auth = self.config.auth if auth is None else auth
        cert = self.config.cert if cert is None else cert
        token = self.config.token if token is None else token
        ca_cert = self.config.ca_cert if ca_cert is None else ca_cert
        ca_cert_data = self.config.ca_cert_data if ca_cert_data is None else ca_cert_data

        r = HttpRequest(
            method=method,
            host=host,
            url=url,
            auth=auth,
            cert=cert,
            ca_cert=ca_cert,
            ca_cert_data=ca_cert_data,
            data=data,
            token=token
        )

        try:
            return r.send()
        except IOError as err:
            raise BadRequestException('K8sObject: IOError: {0}'.format(err))

    def list(self):
        state = self.request(method='GET')
        if not state.get('status'):
            raise Exception('K8sObject: Could not fetch list of objects of type: [ {0} ]'.format(self.obj_type))
        if not state.get('success'):
            status = state.get('status', '')
            state_data = state.get('data', dict())
            reason = state_data['message'] if 'message' in state_data else state_data
            message = 'K8sObject: CREATE failed : HTTP {0} : {1}'.format(status, reason)
            if int(status) == 401:
                raise UnauthorizedException(message)
            if int(status) == 409:
                raise AlreadyExistsException(message)
            if int(status) == 422:
                raise UnprocessableEntityException(message)
            raise BadRequestException(message)
        return state.get('data', dict()).get('items', list())

    def get_model(self):
        if self.name is None:
            raise SyntaxError('K8sObject: name: [ {0} ] must be set to fetch the object.'.format(self.name))

        url = '{base}/{name}'.format(base=self.base_url, name=self.name)
        state = self.request(method='GET', url=url)

        if not state.get('success'):
            status = state.get('status', '')
            reason = state.get('data', dict()).get('message', None)
            message = 'K8sObject: GET [ {0}:{1} ] failed: HTTP {2} : {3} '.format(self.obj_type, self.name, status,
                                                                                  reason)
            raise NotFoundException(message)

        model = state.get('data')
        return model

    def get_with_params(self, data=None):
        if not is_valid_dict(data):
            raise SyntaxError('K8sObject.get_with_params(): data: [ {0} ] is invalid.'.format(data))
        url = '{base}'.format(base=self.base_url)
        state = self.request(method='GET', url=url, data=data)
        return state.get('data', None).get('items', list())

    def create(self):
        if self.name is None:
            raise SyntaxError('K8sObject: name: [ {0} ] must be set to CREATE the object.'.format(self.name))

        # HTTP 500 : resourceVersion may not be set on objects to be created
        if self.model.metadata.resource_version is not None:
            self.model.metadata.resource_version = None

        url = '{base}'.format(base=self.base_url)
        state = self.request(method='POST', url=url, data=self.serialize())

        if not state.get('success'):
            status = state.get('status', '')
            state_data = state.get('data', dict())
            reason = state_data['message'] if 'message' in state_data else state_data
            message = 'K8sObject: CREATE failed : HTTP {0} : {1}'.format(status, reason)
            if int(status) == 401:
                raise UnauthorizedException(message)
            if int(status) == 409:
                raise AlreadyExistsException(message)
            if int(status) == 422:
                raise UnprocessableEntityException(message)
            raise BadRequestException(message)
        return self

    def update(self):
        if self.name is None:
            raise SyntaxError('K8sObject: name: [ {0} ] must be set to UPDATE the object.'.format(self.name))

        # HTTP 409: Cannot apply update if UID in precondition and updated object.meta
        if self.model.metadata.uid is not None:
            self.model.metadata.uid = None

        url = '{base}/{name}'.format(base=self.base_url, name=self.name)
        state = self.request(method='PUT', url=url, data=self.serialize())

        if not state.get('success'):
            status = state.get('status', '')
            reason = state.get('data', dict()).get('message', None)
            message = 'K8sObject: UPDATE failed: HTTP {0} : {1}'.format(status, reason)
            if int(status) == 404:
                raise NotFoundException(message)
            if int(status) == 422:
                raise UnprocessableEntityException(message)
            raise BadRequestException(message)

        return self

    def delete(self):
        if self.name is None:
            raise SyntaxError('K8sObject: name: [ {0} ] must be set to DELETE the object.'.format(self.name))

        url = '{base}/{name}'.format(base=self.base_url, name=self.name)
        state = self.request(method='DELETE', url=url, data=DeleteOptions().serialize())

        if not state.get('success'):
            status = state.get('status', '')
            reason = state.get('data', dict()).get('message', None)
            message = 'K8sObject: DELETE failed: HTTP {0} : {1}'.format(status, reason)
            if int(status) == 404:
                raise NotFoundException(message)
            raise BadRequestException(message)

        return self
