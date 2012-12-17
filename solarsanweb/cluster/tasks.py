
import celery
from celery import chain, group, task, chord, Task
from celery.task import periodic_task, PeriodicTask
from celery.schedules import crontab
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from datetime import datetime, timedelta
import time
from django.utils import timezone
#from django.core.files.storage import Storage
#from django.core.exceptions import ObjectDoesNotExist
#from django import db
#from django.db import import autocommit, commit, commit_manually, commit_on_success, \
#    is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty
import os
import logging
import sys

from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes, \
    LoggedException
from django.conf import settings
import storage.target
import rtslib
import beacon

from solarsan.models import Config
from storage.models import Pool, Dataset, Filesystem, Volume, Snapshot
from .models import Node, Peer

import solarsan.signals



"""
Config
"""


def get_config():
    return Config.objects.get(name='cluster')


"""
Neighbor Node
"""

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


@task
def probe_node(host):
    """Probes a discovered node for info"""
    api = ClusterAPI(host=host)

    try:
        probe = api.probe()
    except:
        logger.error('Cluster discovery (probe \'%s\'): Failed.', host)
        return False
    logger.info("Cluster discovery (probe '%s'): Hostname is '%s'.", host, probe['hostname'])

    # TODO Each node should prolly get a UUID, glusterfs already assigns one, but maybe we
    # should do it a layer above.
    cnode, created = Node.objects.get_or_create(hostname=probe['hostname'])
    cnode.interfaces = dict(probe['interfaces'])
    cnode['last_seen'] = timezone.now()
    cnode.save()

    return True


@periodic_task(run_every=timedelta(seconds=settings.SOLARSAN_CLUSTER['discovery']))
def discover_neighbor_nodes():
    """ Probes for new cluster nodes """
    # Beacon discovery
    port = settings.SOLARSAN_CLUSTER['port']
    key = settings.SOLARSAN_CLUSTER['key']

    logger.info("Probing for new cluster nodes (port=%s,key=%s)", port, key)
    nodes = beacon.find_all_servers(port, key)

    if '127.0.0.1' not in nodes:
        logger.error("Didn't find 127.0.0.1 in discovery, is the beacon service started?")

    # Call Query task for each host to probe their API
    c = group(probe_node.s(node) for node in nodes)
    c()


# TODO Cluster Node Cleanup Periodic Task (run weekly/monthly)
@periodic_task(run_every=timedelta(days=7))
def cleanup_ancient_discovered_nodes():
    logger.warning("TODO")


"""
Clustered Pool LUN Export
"""


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
    tpg.set_attribute('authentication', 0)
    portal = tpg.network_portal('0.0.0.0', 3290)

    luns = list(tpg.luns)
    logger.info("luns=%s", luns)

    for pool in Pool.objects_clustered.filter(enabled=False):
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


"""
Startup
"""


def startup(**kwargs):
    discover_neighbor_nodes.delay()
    export_clustered_pool_vdevs.delay()

solarsan.signals.startup.connect(startup, sender='solarsan')
