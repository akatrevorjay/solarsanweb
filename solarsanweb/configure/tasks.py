from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Volume, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time, logging
from datetime import timedelta
from django.utils import timezone
#from django.core.files.storage import Storage
from django.core.exceptions import ObjectDoesNotExist
#from django import db
#from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty

"""
Cluster Discovery / Beacon
"""

from django.core.cache import cache
from django.conf import settings
#from configure.models import ClusterNode
import beacon
#import json

##
## TODO RESTful service perhaps ysing piston to get information from one SAN to the other after discovery is completed.
##

class Cluster_Node_Discovery( PeriodicTask ):
    """ Probes for new cluster nodes """
    run_every = timedelta( seconds=settings.SOLARSAN_CLUSTER['discovery'] )
    def run( self, *args, **kwargs ):
        logger = self.get_logger( **kwargs )
        logger.info( "Cluster discovery: Probing for new cluster nodes (port=%s,key=%s)",
                     settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )

        DiscoveredClusterNodes = {'nodes': beacon.find_all_servers( settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] ),
                                  'ts': timezone.now(), }

        cache.set( 'RecentlyDiscoveredClusterNodes', DiscoveredClusterNodes, settings.SOLARSAN_CLUSTER['discovery'] )
        if len( DiscoveredClusterNodes['nodes'] ) > 0:
            logger.debug( "Cluster discovery: Found: %s", DiscoveredClusterNodes )


## FUCK Make this start on startup, spawns it's own thread, no need to pay attention to it after it's started
class Cluster_Node_Beacon( Task ):
    """ Controls cluster beacon service """
    b = beacon.Beacon( settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )
    def run( self, *args, **kwargs ):
        logger = self.get_logger( **kwargs )
        logger.debug( "Starting Cluster Beacon.." )

        self.b.daemon = True
        self.b.start()

        logger.info( "Started Cluster Beacon." )




