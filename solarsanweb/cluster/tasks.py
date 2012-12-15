from celery import group
from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask, TaskSet
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from storage.models import Pool, Dataset, Filesystem, Volume, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time
from datetime import timedelta
from django.utils import timezone
#from django.core.files.storage import Storage
from django.core.exceptions import ObjectDoesNotExist
#from django import db
#from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty
from solarsan.models import Config
import storage.target
import rtslib
import os
import logging
import sys

from .models import Node, Peer

import solarsan.signals


"""
Cluster Discovery / Beacon
"""

from django.core.cache import cache
from django.conf import settings
#from cluster.models import Node
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
        return self._get('cluster/probe/.json')


class Cluster_Node_Query(Task):
    def run(self, *args, **kwargs):
        # Probe single host (say after beacon discovery)
        host =  kwargs.get('host')
        if not host:
            raise Exception('No host specified')
        api = ClusterAPI(host=host)
        try:
            probe = api.probe()
        except:
            logger.error( 'Cluster discovery (probe \'%s\'): Failed.', host)
            return False
        logger.debug( "Cluster discovery (probe '%s'): Hostname is '%s'.", host, probe['hostname'])
        #logger.debug("Probe=%s", probe)

        # TODO Each node should prolly get a UUID, glusterfs already assigns one, but maybe we should do it a layer above.
        cnode, created = Node.objects.get_or_create(hostname=probe['hostname'])
        cnode.interfaces = dict(probe['interfaces'])
        cnode['last_seen'] = timezone.now()
        cnode.save()

        return True


class Cluster_Node_Discover(PeriodicTask):
    """ Probes for new cluster nodes """
    run_every = timedelta( seconds=settings.SOLARSAN_CLUSTER['discovery'] )
    def run( self, *args, **kwargs ):
        # Beacon discovery
        logger.info( "Probing for new cluster nodes (port=%s,key=%s)",
                     settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )

        nodes = beacon.find_all_servers( settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'] )

        if '127.0.0.1' not in nodes:
            logger.error("Didn't find 127.0.0.1 in discovery, is the beacon service started?")

        # Call Query task for each host to probe their API
        for node_ip in nodes:
            logger.debug("node_ip=%s", node_ip)
            Cluster_Node_Query.delay(host=node_ip)
        #s = group([Cluster_Node_Query.subtask(host=node_ip) for node_ip in nodes])
        #s.apply_async()


## TODO Cluster Node Cleanup Periodic Task (run weekly/monthly)
#class Cluster_Node_Cleanup(PeriodicTask):


def get_config():
    return Config.objects.get(name='cluster')


def get_or_create_target(wwn=None, fm=None):
    if not fm:
        fm = 'iscsi'
    fm = storage.target.get_fabric_module(fm)
    if wwn:
        target = rtslib.Target(fm, wwn)
    else:
        target = rtslib.Target(fm)
    return target


@task
def export_clustered_pool_vdevs():
    cluster_conf = get_config()
    target = get_or_create_target(wwn=getattr(cluster_conf, 'target_wwn', None),
                                  fm=getattr(cluster_conf, 'target_fm', None))
    if not hasattr(cluster_conf, 'target_wwn'):
        cluster_conf.target_wwn = target.wwn
        cluster_conf.save()
    tpg = rtslib.TPG(target, tag=1)
    tpg.enable = 1
    portal = tpg.network_portal('0.0.0.0', 3290)

    luns = list(tpg.luns)
    logger.info("luns=%s", luns)

    # TODO Make default manager for Pool pay attention to enabled=bool
    for pool in Pool.objects_including_disabled.filter(is_clustered=True, enabled=False):
        logger.info("pool=%s", pool)
        for vdev in pool.vdevs:
            export_clustered_pool_vdev(pool, tpg, vdev)


@task
def export_clustered_pool_vdev(pool, tpg, vdev):
    if vdev.is_parent:
        for child in vdev.children:
            export_clustered_pool_vdev(pool, tpg, child)
        return

    logger.info("vdev path=%s vdev=%s", vdev.path, vdev)

    if not os.path.exists(vdev.path):
        logger.error("Vdev path does not exist: '%s'", vdev.path)
        return False

    bso = storage.target.get_or_create_bso("cluster_%s_%s" % (pool.name, vdev.guid), dev=vdev.path)
    # TODO Exceptions
    if not bso:
        return
    lun = storage.target.get_or_create_bso_lun_in_tpg(bso, tpg)

    logger.info("vdev path=%s bso=%s lun=%s", vdev.path, bso, lun)


def startup(**kwargs):
    export_clustered_pool_vdevs.delay()

solarsan.signals.startup.connect(startup)
