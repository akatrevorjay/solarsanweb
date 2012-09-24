from celery.task import periodic_task, task
from celery.task.base import PeriodicTask, Task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from solarsan.utils import convert_human_to_bytes
import os
import time
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

import zfs
#from objects import Pool, Dataset, Filesystem, Volume
import storage.models as m
from storage.models import Pool, Dataset, Filesystem, Volume

import cube_python


"""
Pool IOStats
"""


class PoolIOStats(PeriodicTask):
    """ Periodic task to log iostats per pool to db. """
    run_every = timedelta(seconds=30)
    def run(self, capture_length=30, *args, **kwargs):
        iostats = zfs.pool.iostat(capture_length=capture_length)
        #timestamp_end = datetime.utcnow()
        timestamp_end = timezone.now()

        e = cube_python.Emitter(settings.CUBE_COLLECTOR_URL)
        for i in iostats:
            pool = Pool(i)
            if not pool.exists():
                logger.error('Got data for an unknown pool "%s"', i)
                continue

            event = {'time': iostats[i]['timestamp'],
                     'type': 'pool_iostat',
                     'data': {
                         'pool':        pool.name,
                         #'duration':    timestamp_end - iostats[i]['timestamp']
                         },
                     }

            for j in ['alloc', 'free', 'bandwidth_read', 'bandwidth_write', 'iops_read', 'iops_write']:
                # Convert human readable to bytes
                event['data'][j] = int(convert_human_to_bytes(iostats[i][j]))

            ret = e.send(event)
            #logger.debug('event=%s ret=%s', event, ret)
        e.close()



"""
Import pool/dataset info from system into DB
"""


#class ImportZFSMetadata(Task):
class Import_ZFS_Metadata2(PeriodicTask):
    run_every = timedelta(minutes=30)
    def run(self, *args, **kwargs):
        for pool in m.Pool.list(ret=list):
            if not getattr(pool, 'id', None):
                logger.warning("Found new ZFS storage pool '%s'", pool.name)
                pool.reload_zdb()
                pool.save()

            children = {}
            for k, v in m.ZFS_TYPE_MAP.iteritems():
                if not getattr(v, 'objects', None):
                    continue
                children[k] = v.objects.filter(name__startswith='%s/' % pool.name)
                children[k].update(set__importing=True, multi=True)

            pool_fs = pool.filesystem
            self.walk(pool, pool_fs)

            #children.filter(importing=True, enabled__ne=False).update(set__enabled=False)
            #children.filter(importing=True).delete(modified__lt=timezone.now() -
            #                                            datetime.timedelta(days=7))

            for k in children.iterkeys():
                children[k].filter(importing=True).delete()

    def walk(self, pool, parent):
        filesystems = []
        #parent_regex = re.compile('^%s/[^/]+$' % parent.name)

        if not getattr(parent, 'id', None):
            logger.warning("Found new dataset '%s'", parent.name)
            parent.pool = pool
            parent.save()

        for dataset in parent.children(ret=list):
            #logger.debug("Dataset %s", dataset)
            if not getattr(dataset, 'id', None):
                logger.warning("Found new dataset '%s'", dataset.name)
            else:
                dataset.update(unset__importing=True)
            dataset.pool = pool
            dataset.save()
            if dataset.type == 'filesystem':
                filesystems.append(dataset)

        for fs in filesystems:
            # Run recursively on this node's children
            self.walk(pool, fs)

