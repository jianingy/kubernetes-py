#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is subject to the terms and conditions defined in
# file 'LICENSE.md', which is part of this source code package.
#

from kubernetes.K8sObject import K8sObject
from kubernetes.K8sDeployment import K8sDeployment
from kubernetes.K8sReplicationController import K8sReplicationController
from kubernetes.K8sExceptions import NotFoundException
from kubernetes.models.v1.HorizontalPodAutoscaler import HorizontalPodAutoscaler
import subprocess


class K8sHorizontalPodAutoscaler(K8sObject):

    def __init__(self, config=None, name=None):

        super(K8sHorizontalPodAutoscaler, self).__init__(
            config=config,
            obj_type='HorizontalPodAutoscaler',
            name=name
        )

    # -------------------------------------------------------------------------------------  override

    def create(self):
        super(K8sHorizontalPodAutoscaler, self).create()
        self.get()
        return self

    def update(self):
        super(K8sHorizontalPodAutoscaler, self).update()
        self.get()
        return self

    def list(self, pattern=None):
        ls = super(K8sHorizontalPodAutoscaler, self).list()
        hpas = list(map(lambda x: HorizontalPodAutoscaler(x), ls))
        if pattern is not None:
            hpas = list(filter(lambda x: pattern in x.name, hpas))
        k8s = []
        for x in hpas:
            z = K8sHorizontalPodAutoscaler(config=self.config, name=x.name)
            z.model = x
            k8s.append(z)
        return k8s

    # ------------------------------------------------------------------------------------- get

    def get(self):
        self.model = HorizontalPodAutoscaler(self.get_model())
        return self

    # ------------------------------------------------------------------------------------- cpu_percent

    @property
    def cpu_percent(self):
        return self.model.spec.cpu_utilization

    @cpu_percent.setter
    def cpu_percent(self, pct=None):
        self.model.spec.cpu_utilization = pct

    # ------------------------------------------------------------------------------------- min replicas

    @property
    def min_replicas(self):
        return self.model.spec.min_replicas

    @min_replicas.setter
    def min_replicas(self, min=None):
        self.model.spec.min_replicas = min

    # ------------------------------------------------------------------------------------- max replicas

    @property
    def max_replicas(self):
        return self.model.spec.max_replicas

    @max_replicas.setter
    def max_replicas(self, max=None):
        self.model.spec.max_replicas = max
