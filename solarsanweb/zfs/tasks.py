from celery.task import periodic_task, task
from celery.task.base import PeriodicTask, Task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from solarsan.utils import convert_human_to_bytes
import os, time
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

#from zfs.models import Pool
#from zfs.db import PoolDocument
from zfs.objects import Pool, Dataset, Filesystem, Volume
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

