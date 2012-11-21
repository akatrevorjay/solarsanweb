#from celery.task import periodic_task, task, chord
#from celery.task.base import PeriodicTask, Task
#from celery.task.sets import subtask
#from datetime import timedelta, datetime
#import time
#from django.utils import timezone
#from django.core.files.storage import Storage
#from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
#import re


from celery.task import task, Task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from django.conf import settings
import os


#from storage.models import Pool, Filesystem, Volume, Snapshot
from solarsan.utils import FormattedException, LoggedException


from backup.util import optimize, recursive_replicate
from backup.transports.common import ZFSConnection


"""
Main
"""

#BUFSIZE = 1048576
BUFSIZE = 4096
SSH_KEY = '/opt/solarsanweb/conf/id_rsa'


class DatasetDoesNotExist(LoggedException):
    #def blah():
    #    LoggedException("Source dataset '%s' does not exist" % dataset.name)
    pass


@task
def replicate(source_dataset, dry_run=False):

    # HACK LocSol Backup router should handle this.
    dest_user = 'root'
    dest_host = '192.168.122.167'
    dest_port = 22
    dest_base = 'dpool/dest'

    src_dataset = source_dataset.name
    dest_dataset = '%s/%s' % (dest_base, settings.SERVER_NAME)

    src_conn = ZFSConnection(
        host='localhost',
        bufsize=BUFSIZE)
    dest_conn = ZFSConnection(
        username=dest_user,
        hostname=dest_host,
        port=dest_port,
        password='',
        private_key=SSH_KEY,
        bufsize=BUFSIZE)

    logger.info("Starting replication job: '%s' to '%s@%s:%s'",
                src_dataset, dest_user, dest_host, dest_dataset)

    # Check if source exists
    logger.debug('Checking that source filesystem exists')
    #if not source_dataset.exists():
    #    raise DatasetDoesNotExist(source_dataset)
    try:
        source_dataset = src_conn.pools.lookup(src_dataset)
    except KeyError:
        logger.error("Source dataset '%s' does not exist.",
                     src_dataset)
        return False

    # Check if dest exists
    logger.debug('Checking that dest filesystem exists')
    try:
        destination_dataset = dest_conn.pools.lookup(dest_dataset)
    except KeyError:
        logger.error("Destination dataset '%s' does not exist.",
                     dest_dataset)
        return False

    # Figure out our plan
    operation_schedule = recursive_replicate(source_dataset,
                                             destination_dataset)
    # Optimize it
    optimized_operation_schedule = optimize(operation_schedule)

    # Build the send/receive initial args
    send_opts = []
    receive_opts = []
    if dry_run:
        receive_opts.append('-n')

    # Run through schedule
    for (op, src, dst, srcs, dsts) in optimized_operation_schedule:
        logger.debug('op=%s src=%s dst=%s srcs=%s dsts=%s',
                     op, src, dst, srcs, dsts)

        source_dataset_path = src.get_path()
        if srcs:
            this_send_opts = ['-I', '@' + srcs.name]
        else:
            this_send_opts = []

        if dst:
            destination_dataset_path = dst.get_path()
        else:
            commonbase = os.path.commonprefix([src.get_path(),
                                               source_dataset.get_path()])
            remainder = src.get_path()[len(commonbase):]
            destination_dataset_path = destination_dataset.get_path() + remainder
        destination_snapshot_path = dsts.get_path()

        logger.info("Replicating '%s' to '%s' with base=%s, target=%s",
                    source_dataset_path, destination_dataset_path,
                    srcs, dsts)

        # finagle the send() part of transfer by
        # manually selecting incremental sending of intermediate snapshots
        # rather than sending of differential snapshots
        # which would happen if we used the fromsnapshot= parameter to transfer()

        src_conn.transfer(
            dest_conn,
            s=destination_snapshot_path,
            d=destination_dataset_path,
            bufsize=BUFSIZE,
            send_opts=send_opts + this_send_opts,
            receive_opts=receive_opts,
        )

    logger.info('Replication job complete.')


class Backup(Task):
    def run(self, dataset, **kwargs):
        if not dataset.exists():
            raise Exception("Source dataset '%s' does not exist" % dataset.name)
        #bufsize = 1048576
        bufsize = 4096
        dry_run = False
        verbose = True

        # HACK Get this from LocSol backup router
        dest_user = 'root'
        dest_host = '192.168.122.167'
        dest_port = 22
        # HACK Get this from LocSol backup router
        dest_base = 'dpool/dest'

        source_dataset = dataset.name
        destination_dataset = '%s/%s' % (dest_base, settings.SERVER_NAME)

        src_conn = ZFSConnection(host='localhost', bufsize=bufsize)
        dest_conn = ZFSConnection(
            username=dest_user,
            hostname=dest_host,
            port=dest_port,
            password='',
            private_key='/opt/solarsanweb/conf/id_rsa',
            bufsize=bufsize,
        )

        logger.info('Replicating %s to %s::%s', dataset.name, dest_host, dest_base)

        logger.debug('Checking that source filesystem exists')
        try:
            source_dataset = src_conn.pools.lookup(source_dataset)
        except KeyError:
            logger.error('Source dataset does not exist.')
            return False

        logger.debug('Checking that dest filesystem exists')
        try:
            destination_dataset = dest_conn.pools.lookup(destination_dataset)
        except KeyError:
            import ipdb
            ipdb.set_trace()
            logger.error('Destination dataset does not exist.')
            return False

        operation_schedule = recursive_replicate(source_dataset,
                                                 destination_dataset)

        optimized_operation_schedule = optimize(operation_schedule)

        send_opts = ['-R']
        receive_opts = []
        if dry_run:
            receive_opts.append('-n')
        if verbose:
            send_opts.append('-v')
            receive_opts.append('-v')

        for (op, src, dst, srcs, dsts) in optimized_operation_schedule:

                # assert 0, (op,src,dst,srcs,dsts)

            source_dataset_path = src.get_path()
            if srcs:
                this_send_opts = ['-I', '@' + srcs.name]
            else:
                this_send_opts = []

            if dst:
                destination_dataset_path = dst.get_path()
            else:
                commonbase = os.path.commonprefix([src.get_path(),
                                                   source_dataset.get_path()])
                remainder = src.get_path()[len(commonbase):]
                destination_dataset_path = destination_dataset.get_path() + remainder
            destination_snapshot_path = dsts.get_path()

            logger.info('Recursively replicating %s to %s' % (
                source_dataset_path, destination_dataset_path))
            logger.info('Base snapshot available in destination: %s' % srcs)
            logger.info('Target snapshot available in source:    %s' % dsts)

            # finagle the send() part of transfer by
            # manually selecting incremental sending of intermediate snapshots
            # rather than sending of differential snapshots
            # which would happen if we used the fromsnapshot= parameter to transfer()

            src_conn.transfer(
                dest_conn,
                s=destination_snapshot_path,
                d=destination_dataset_path,
                bufsize=bufsize,
                send_opts=send_opts + this_send_opts,
                receive_opts=receive_opts,
            )

        logger.info('Replication complete.')




#PROPS = {
#        'lock':     'solarsan:replication_lock',        # True/False
#        'status':   'solarsan:replication_status',      # Status of replication
#        'type':     'solarsan:replication_type',        # Type of replication
#        'to':       'solarsan:replication_to',          # Snapshot that is being replicated toward
#        'from':     'solarsan:replication_from',        # Snapshot that is being replicated from
#}

#class BackupDataset(zfs.objects.Dataset):
#    def _get_prop(self, prop):
#        if prop in PROPS:
#            prop = PROPS[prop]
#        super(backupDataset, self)._get_prop(prop)

#def get_prop(prop):
#    return

#class ReplicationType(object):
#    recursive = True
#    def __new__(cls, *args, **kwargs):
#        if 'snap_from' in kwargs:
#            subclass = IncrementalReplication
#        else:
#            subclass = FullReplication
#        return super(ReplicationType, cls).__new__(subclass, *args, **kwargs)
#    def __init__(self, *args, **kwargs):
#        self.dt = datetime.now()
#
#        self.dataset = zfs.objects.Dataset(kwargs['dataset'])
#        if not self.dataset.exists():
#            raise Exception('Dataset %s does not exist' % self.dataset.name)
#
#        self.col = get_database()[ReplicationJob.collection_name]
#        for job in ReplicationJob.find({'dataset': dataset, 'active': True}):
#            # TODO Somehow check if this job is really active or not
#            job.update({'$unset': {'active': 1}})
#
#        # Check for lock on dataset
#        self.lock = dataset.props[PROPS['lock']]
#        if lock == True:
#            ## TODO Check for currently running backup and act accordingly (exit quietly)
#            replication_id = dataset.props[PROPS['id']]
#
#            status = dataset.props[PROPS['status']]
#            self.snap_from = dataset.props[PROPS['snap_from']]
#            self.snap_to = dataset.props[PROPS['snap_to']]
#        self.snap_to = zfs.objects.Dataset(kwargs.get('snap_to', None))
#        # If we weren't given a snap_to, create a new snapshot to use
#        if self.snap_to == None:
#            self.snap_to = self.dataset.snapshot(self.dt.strftime('solarsan:replication-%F-%I:%M%P'), recursive=self.recursive)
#        if not self.snap_to.exists():
#            raise Exception('To snapshot %s does not exist' % self.snap_to.name)
#
#    def replicate(self):
#        pass
#
#class IncrementalReplication(ReplicationType):
#    def __init__(self, dataset=None, snap_from=None, snap_to=None):
#        super(IncrementalReplication, self).__init__(dataset=None, snap_to=None, **kwargs)
#        self.snap_from = zfs.objects.Dataset(kwargs['snap_from'])
#        if not self.snap_from.exists():
#            raise Exception('From snapshot %s does not exist' % self.snap_from.name)
#
#
#class FullReplication(ReplicationType):
#    def __init__(self, dataset=None, snap_to=None, **kwargs):
#        super(FullReplication, self).__init__(parent)
#
#
#class BackupDataset(zfs.objects.Dataset):
#    def __init__(self, *args, **kwargs):
#        super(BackupDataset, self).__init__(self, *args, **kwargs)
#
#        # Check for lock on dataset
#        lock = dataset.props[PROPS['lock']]
#        if lock == True:
#            ## TODO Check for currently running backup and act accordingly (exit quietly)
#            snap_to = zfs.objects.Dataset(dataset.props[PROPS['to']])
#            type = dataset.props[PROPS['type']]
#
#            if not snap_to.exists():
#                    logger.error('Replication lock on %s is invalid. The snap to replicate to (%s) does not exist.', dataset, snap_to.name)
#                    raise Exception('Invalid lock found on %s' % dataset)
#
#            if type == 'incremental':
#                snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])
#
#                if not snap_from.exists():
#                    logger.error('Replcation lock on %s is invalid. The snap to replicate from (%s) does not exist.', dataset, snap_from)
#                    raise Exception('Invalid lock found on %s' % dataset)
#
#                logger.warning('Found existing lock on %s from %s to %s', dataset, snap_from, snap_to, type)
#            else:
#                type = 'full'
#                logger.warning('Found existing lock on %s to %s', dataset, snap_to)
#            logger.info('Continuing previous %s replication', type)
#
#
#class Backup(Task):
#    def run(self, *args, **kwargs):
#        dataset = zfs.objects.Dataset(args[0])
#
#        # Check for lock on dataset
#        lock = dataset.props[PROPS['lock']]
#        if lock == True:
#            ## TODO Check for currently running backup and act accordingly (exit quietly)
#            snap_to = zfs.objects.Dataset(dataset.props[PROPS['to']])
#            type = dataset.props[PROPS['type']]
#
#            if not snap_to.exists():
#                    logger.error('Replication lock on %s is invalid. The snap to replicate to (%s) does not exist.', dataset, snap_to.name)
#                    raise Exception('Invalid lock found on %s' % dataset)
#
#            if type == 'incremental':
#                snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])
#
#                if not snap_from.exists():
#                    logger.error('Replcation lock on %s is invalid. The snap to replicate from (%s) does not exist.', dataset, snap_from)
#                    raise Exception('Invalid lock found on %s' % dataset)
#
#                logger.warning('Found existing lock on %s from %s to %s', dataset, snap_from, snap_to, type)
#            else:
#                type = 'full'
#                logger.warning('Found existing lock on %s to %s', dataset, snap_to)
#            logger.info('Continuing previous %s replication', type)
#
#            if snap_to.exists():
#                type = dataset.props[PROPS['type']]
#                if type == 'incremental':
#                    snap_from = zfs.objects.Dataset(dataset.props[PROPS['from']])
#                    if snap_from.exists():
#                        logger.warning('Continuing replication on %s from %s to %s', dataset, snap_from, snap_to)
#            else:
#                logger.error('Found old lock on %s to a non-existent snapshot %s; Cleaning up and starting over.', dataset, snap_to)
#                snap_to = None
#
#        # If we don't already have a destination snap to replicate toward, create a new snapshot and use that
