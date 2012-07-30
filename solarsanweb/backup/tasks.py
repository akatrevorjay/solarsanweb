from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.utils.log import get_task_logger
from celery.task.sets import subtask
logger = get_task_logger(__name__)

from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time
from datetime import timedelta
from django.utils import timezone
#from django.core.files.storage import Storage

from django_mongokit import get_database, connection
from django_mongokit.document import DjangoDocument

from storage.models import zPool, zDataset
import re
import zfs


PROPS = {
        'lock':     'solarsan:replication_lock',        # True/False
        'status':   'solarsan:replication_status',      # Status of replication
        'type':     'solarsan:replication_type',        # Type of replication
        'to':       'solarsan:replication_to',          # Snapshot that is being replicated toward
        'from':     'solarsan:replication_from',        # Snapshot that is being replicated from
}

#class BackupDataset(zfs.objects.Dataset):
#    def _get_prop(self, prop):
#        if prop in PROPS:
#            prop = PROPS[prop]
#        super(backupDataset, self)._get_prop(prop)

#def get_prop(prop):
#    return

import datetime

class ReplicationType(object):
    recursive = True
    def __new__(cls, *args, **kwargs):
        if 'snap_from' in kwargs:
            subclass = IncrementalReplication
        else:
            subclass = FullReplication
        return super(ReplicationType, cls).__new__(subclass, *args, **kwargs)
    def __init__(self, *args, **kwargs):
        self.dt = datetime.datetime.now()

        self.dataset = zfs.objects.Dataset(kwargs['dataset'])
        if not self.dataset.exists():
            raise Exception('Dataset %s does not exist' % self.dataset.name)

        self.col = get_database()[ReplicationJob.collection_name]
        for job in ReplicationJob.find({'dataset': dataset, 'active': True}):
            # TODO Somehow check if this job is really active or not
            job.update({'$unset': {'active': 1}})

        # Check for lock on dataset
        self.lock = dataset.props[PROPS['lock']]
        if lock == True:
            ## TODO Check for currently running backup and act accordingly (exit quietly)
            replication_id = dataset.props[PROPS['id']]

            status = dataset.props[PROPS['status']]
            self.snap_from = dataset.props[PROPS['snap_from']]
            self.snap_to = dataset.props[PROPS['snap_to']]
        self.snap_to = zfs.objects.Dataset(kwargs.get('snap_to', None))
        # If we weren't given a snap_to, create a new snapshot to use
        if self.snap_to == None:
            self.snap_to = self.dataset.snapshot(self.dt.strftime('solarsan:replication-%F-%I:%M%P'), recursive=self.recursive)
        if not self.snap_to.exists():
            raise Exception('To snapshot %s does not exist' % self.snap_to.name)

    def replicate(self):
        pass

class IncrementalReplication(ReplicationType):
    def __init__(self, dataset=None, snap_from=None, snap_to=None):
        super(IncrementalReplication, self).__init__(dataset=None, snap_to=None, **kwargs)
        self.snap_from = zfs.objects.Dataset(kwargs['snap_from'])
        if not self.snap_from.exists():
            raise Exception('From snapshot %s does not exist' % self.snap_from.name)


class FullReplication(ReplicationType):
    def __init__(self, dataset=None, snap_to=None, **kwargs):
        super(FullReplication, self).__init__(parent)


class BackupDataset(zfs.objects.Dataset):
    def __init__(self, *args, **kwargs):
        super(BackupDataset, self).__init__(self, *args, **kwargs)

        # Check for lock on dataset
        lock = dataset.props[PROPS['lock']]
        if lock == True:
            ## TODO Check for currently running backup and act accordingly (exit quietly)
            snap_to = zfs.objects.Dataset(dataset.props[PROPS['to']])
            type = dataset.props[PROPS['type']]

            if not snap_to.exists():
                    logger.error('Replication lock on %s is invalid. The snap to replicate to (%s) does not exist.', dataset, snap_to.name)
                    raise Exception('Invalid lock found on %s' % dataset)

            if type == 'incremental':
                snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])

                if not snap_from.exists():
                    logger.error('Replcation lock on %s is invalid. The snap to replicate from (%s) does not exist.', dataset, snap_from)
                    raise Exception('Invalid lock found on %s' % dataset)

                logger.warning('Found existing lock on %s from %s to %s', dataset, snap_from, snap_to, type)
            else:
                type = 'full'
                logger.warning('Found existing lock on %s to %s', dataset, snap_to)
            logger.info('Continuing previous %s replication', type)


class Backup(Task):
    def run(self, *args, **kwargs):
        dataset = zfs.objects.Dataset(args[0])

        # Check for lock on dataset
        lock = dataset.props[PROPS['lock']]
        if lock == True:
            ## TODO Check for currently running backup and act accordingly (exit quietly)
            snap_to = zfs.objects.Dataset(dataset.props[PROPS['to']])
            type = dataset.props[PROPS['type']]

            if not snap_to.exists():
                    logger.error('Replication lock on %s is invalid. The snap to replicate to (%s) does not exist.', dataset, snap_to.name)
                    raise Exception('Invalid lock found on %s' % dataset)

            if type == 'incremental':
                snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])

                if not snap_from.exists():
                    logger.error('Replcation lock on %s is invalid. The snap to replicate from (%s) does not exist.', dataset, snap_from)
                    raise Exception('Invalid lock found on %s' % dataset)

                logger.warning('Found existing lock on %s from %s to %s', dataset, snap_from, snap_to, type)
            else:
                type = 'full'
                logger.warning('Found existing lock on %s to %s', dataset, snap_to)
            logger.info('Continuing previous %s replication', type)

            if snap_to.exists():
                type = dataset.props[PROPS['type']]
                if type == 'incremental':
                    snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])
                    if snap_from.exists():
                        logger.warning('Continuing replication on %s from %s to %s', dataset, snap_from, snap_to)
            else:
                logger.error('Found old lock on %s to a non-existent snapshot %s; Cleaning up and starting over.', dataset, snap_to)
                snap_to = None

        # If we don't already have a destination snap to replicate toward, create a new snapshot and use that
