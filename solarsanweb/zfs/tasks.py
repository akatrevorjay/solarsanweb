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

#from zfs.models import Pool
#import zfs.db
from zfs import Pool, Dataset, Filesystem, Volume
import zfs
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

            event = {'type': 'pool_iostat',
                     'time': iostats[i]['timestamp'],
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


#class Import_ZFS_Metadata2(PeriodicTask):
class ImportZFSMetadata(Task):
    #run_every = timedelta(minutes=5)
    def run(self, *args, **kwargs):
        #zfs.db.PoolDocument.objects.all().update(multi=True, importing=True)
        for pool_name,zfs_pool in Pool.list().iteritems():
            pool = zfs_pool.dbo
            #pool.update({'props': zfs_pool.props.all})
            if not getattr(pool, 'id', None):
                logger.warning("Found new ZFS storage pool '%s'", zfs_pool.name)
                pool.save()

            zfs_dataset = zfs_pool.filesystem
            pool_filesystem = self.do_zfs_dataset(pool, zfs_dataset)
            self.do_filesystem_children(pool, zfs_dataset)
    def do_zfs_dataset(self, pool, zfs_dataset, **kwargs):
        #parent = kwargs.get('parent', None)
        dataset = zfs_dataset.dbo

        #if not getattr(dataset, 'id', None):
        #    dataset.save()

        #zfs_dataset.dbm.objects.update(
        #        {'name': zfs_dataset.name},
        #        {'$set': {'type': unicode(zfs_dataset._zfs_type),
        #                  #'props': zfs_dataset.props.all,
        #                  },
        #         '$unset': {'importing': 1}, })

        zfs_dataset.dbm.objects.filter(name__startswith=zfs_dataset.nameall().update(importing=True)

        return dataset
    def do_filesystem_children(self, pool, zfs_dataset_parent):
        filesystems = []
        parent_regex = re.compile('^%s/[^/]+$' % zfs_dataset_parent.name)

        zfs_dataset_parent.dbm.objects.update(
                            {'name': parent_regex},
                            {'$set': {'importing': True, 'last_modified': timezone.now()}
                        },
                    multi=True,
                )

        for zfs_dataset in zfs_dataset_parent.children():
            dataset = self.do_zfs_dataset(pool, zfs_dataset, parent=zfs_dataset_parent)

            if zfs_dataset.type == 'filesystem':
                filesystems.append(zfs_dataset)

        for zfs_dataset in filesystems:
            # Run recursively on this node's children
            self.do_filesystem_children(pool, zfs_dataset)

        zfs_dataset_parent.dbm.objects.remove({'name': parent_regex, 'importing': True})




