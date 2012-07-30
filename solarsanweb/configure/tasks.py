from celery import group
from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask, TaskSet
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Volume, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time
from datetime import timedelta
from django.utils import timezone
#from django.core.files.storage import Storage
from django.core.exceptions import ObjectDoesNotExist
#from django import db
#from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty

from django_mongokit import get_database, connection
from configure.models import ClusterNode

"""
Cluster Discovery / Beacon
"""

from django.core.cache import cache
from django.conf import settings
#from configure.models import ClusterNode
import beacon
#import json

from piston_mini_client import PistonAPI, returns_json

class ClusterAPI(PistonAPI):
    def __init__(self, *args, **kwargs):
        kwargs['service_root'] = '%s://%s/api/v%s' % (kwargs.get('proto', 'https'), kwargs.get('host', 'localhost'), kwargs.get('version', '1'))
        for x in ['proto', 'host', 'version']:
            if x in kwargs:
                kwargs.pop(x)
        kwargs['disable_ssl_validation'] = True
        super(ClusterAPI, self).__init__(*args, **kwargs)

    @returns_json
    def probe(self):
        return self._get('cluster/probe.json')


class Cluster_Node_Query(Task):
    def run(self, *args, **kwargs):
        # Setup DB
        if not hasattr(self, 'col'):
            self.col = get_database()[ClusterNode.collection_name]

        # Probe single host (say after beacon discovery)
        if kwargs.get('host', None) != None:
            host = kwargs['host']
            api = ClusterAPI(host=host)
            try:
                probe = api.probe()
            except:
                logger.error( 'Cluster discovery (probe \'%s\'): Failed.', host)
                return False
            logger.debug( "Cluster discovery (probe '%s'): Hostname is '%s'.", host, probe['hostname'])

            # TODO Each node should prolly get a UUID, glusterfs already assigns one, but maybe we should do it a layer above.
            cnode = self.col.ClusterNode.find_one({'hostname': probe['hostname']})
            if cnode == None:
                cnode = self.col.ClusterNode()
            cnode.update(probe)
            cnode['last_seen'] = timezone.now()
            cnode.save()


class Cluster_Node_Beacon( Task ):
    """ Controls cluster beacon service """
    b = beacon.Beacon( settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )
    def run( self, *args, **kwargs ):
        self.b.daemon = True
        self.b.start()
        logger.info( "Started Cluster Beacon." )


class Cluster_Node_Discover( PeriodicTask ):
    """ Probes for new cluster nodes """
    run_every = timedelta( seconds=settings.SOLARSAN_CLUSTER['discovery'] )
    def run( self, *args, **kwargs ):
        # Beacon discovery
        logger.info( "Cluster discovery: Probing for new cluster nodes (port=%s,key=%s)",
                     settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )

        nodes = beacon.find_all_servers( settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )

        if '127.0.0.1' not in nodes:
            if not settings.DEBUG and cache.get('ClusterBeaconStartedTS'):
                logger.error( "Cluster discovery: Didn't find 127.0.0.1 in discovery; Not starting Cluster Beacon since I already attempted to start it recently.")
            else:
                logger.warning( "Cluster discovery: Didn't find 127.0.0.1 in discovery; Starting Cluster Beacon..")
                Cluster_Node_Beacon.apply()
                cache.set('ClusterBeaconStartedTS', timezone.now(), 300)

        # Call Query task for each host to probe their API
        s = group([Cluster_Node_Query.subtask(host=node_ip) for node_ip in nodes])
        s.apply_async()



## TODO Cluster Node Cleanup Periodic Task (run weekly/monthly)
#class Cluster_Node_Cleanup( PeriodicTask ):





