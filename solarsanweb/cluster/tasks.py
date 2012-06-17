from celery.task.base import Task
import logging
from django.utils import timezone

## netbeacon
import beacon

## TODO Make key configurable
service = {
    'port': 1787,           # 1337 * 1.337
    'key': 'solarsan-key0', # Cluster Key
}

class Prober(Task):
    """ Probes for new cluster nodes """
    def run(self, *args, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Probing for new cluster nodes (port=%s,key=%s)", service['port'], service['key'])

        return beacon.find_all_servers(service['port'], service['key'])

class Beacon(Task):
    """ Controls cluster beacon service """
    b = beacon.Beacon(service['port'], service['key'])
    def run(self, *args, **kwargs):
        logger = self.get_logger(**kwargs)

        action = args[0]

        logger.info("Performing action (%s) on cluster beacon service", action)

        if action == 'start':
            self.b.daemon = True
            self.b.start()
        if action == 'stop':
            return Exception('Not Implemented')

