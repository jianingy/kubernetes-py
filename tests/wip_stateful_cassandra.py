#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is subject to the terms and conditions defined in
# file 'LICENSE.md', which is part of this source code package.
#

from tests import utils
from tests.BaseTest import BaseTest
from kubernetes.K8sReplicationController import K8sReplicationController
from kubernetes.K8sService import K8sService
from kubernetes.models.v1.ReplicationController import ReplicationController
from kubernetes.models.v1.Service import Service
from kubernetes.models.v1beta1.DaemonSet import DaemonSet


class StatefulSetCassandraTests(BaseTest):
    """
    https://github.com/kubernetes/kubernetes/tree/master/examples/storage/cassandra

    Currently incomplete.
    """

    def setUp(self):
        utils.cleanup_services()
        utils.cleanup_rc()
        utils.cleanup_pods()

    def tearDown(self):
        utils.cleanup_services()
        utils.cleanup_rc()
        utils.cleanup_pods()

    def test_cassandra_setup(self):
        svc = Service(utils.cassandra_service())
        k8s_service = utils.create_service(name="cassandra")
        k8s_service.model = svc

        rc = ReplicationController(utils.cassandra_rc())
        k8s_rc = utils.create_rc(name="cassandra")
        k8s_rc.model = rc

        ds = DaemonSet(utils.cassandra_daemonset())
        k8s_ds = utils.create_daemonset(name="cassandra")
        k8s_ds.model = ds

        if utils.is_reachable(k8s_rc.config):
            k8s_service.create()
            k8s_rc.create()
            self.assertIsInstance(k8s_service, K8sService)
            self.assertIsInstance(k8s_rc, K8sReplicationController)
