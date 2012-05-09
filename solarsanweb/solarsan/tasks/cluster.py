from celery.task.base import Task
import logging
from django.utils import timezone
import zfs
from ZeroconfService import ZeroconfService
import time

class Cluster_ZeroConf_Control(Task):
    """ Controls cluster zeroconf services """
    service_cluster = ZeroconfService(name="SolarSan Cluster",
            port=1337, stype="_demo._tcp")
    def run(self, action, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Performing action (%s) on cluster zeroconf services", action)

        if action == 'start':
            self.service_cluster.publish()
        if action == 'stop':
            self.service_cluster.unpublish()



