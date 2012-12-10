
import celery
from celery import chain, group, task, chord, Task
from celery.task import periodic_task, PeriodicTask
from celery.schedules import crontab
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from django.utils import timezone
#from django.core.files.storage import Storage

import os
import time
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings

from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import zfs
from storage.models import Pool, Filesystem, Volume, Snapshot
import storage.models as m


"""
Getters
"""


@task
def get_pools(last_ret=None, cb=None):
    return Pool.list(ret=list)


@task
def get_pool_children(pool):
    pool_name = pool.name
    pool_fs = pool.filesystem
    datasets = pool_fs.list(args=['-r', pool_name], type='all')
    return datasets


"""
Import pool/dataset info from system into DB
"""


@periodic_task(run_every=timedelta(minutes=30))
def sync_zfs():
    c = (mark_all_as_importing.s() | get_pools.s() | sync_pools.s() | cleanup_still_marked_as_importing.s())
    return c()


@task
def mark_all_as_importing():
    for v in [Snapshot, Filesystem, Volume, Pool]:
        if not getattr(v, 'objects_including_disabled', None):
            continue
        v.objects.update(set__importing=True, multi=True)


#@task
#def get_pools(last_ret):
#    return Pool.list(ret=list)


@task
def sync_pools(pools):
    # Use Pool.list() which looks to the filesystem instead of objects
    # which looks to the DB.
    c = group((sync_pool.s(pool) | get_pool_children.s() | sync_datasets.s()) for pool in pools)
    return c().get()


@task
def sync_pool(pool):
    pool_name = pool.name
    if not getattr(pool, 'id', None):
        logger.warning("Found new ZFS storage pool '%s'", pool_name)
    pool.reload_zfs()  # Grab new data from filesystem
    pool.enabled = True
    pool.importing = False
    pool.save()
    return pool


@task
def sync_datasets(datasets):
    #c = group(sync_dataset.s(dataset) for dataset in datasets)
    #return c()
    for dataset in datasets:
        sync_dataset.apply(dataset)


@task
def sync_dataset(dataset):
    if dataset.exists():
        dataset.enabled = True
        dataset.importing = False
        dataset.save()


@task
def cleanup_still_marked_as_importing(last_ret):
    for v in [Snapshot, Filesystem, Volume, Pool]:
        if not getattr(v, 'objects_including_disabled', None):
            continue
        objs = v.objects.filter(importing=True)
        if objs:
            logger.error("Disabling as they seem to no longer exist: %s", objs)
            objs.update(set__enabled=False, multi=True)

        delete_older_than = timezone.now() - timedelta(days=7)
        objs = v.objects_including_disabled.filter(enabled=False, modified__lt=delete_older_than)
        if objs:
            logger.error("Deleting as they've been disabled for over a week: %s", objs)
            objs.delete()


"""
Check pool health
"""


@periodic_task(run_every=timedelta(minutes=30))
def check_pools_health(pools=None):
    logger.info("POOLS: %s", pools)
    if not pools:
        c = (get_pools.s() | check_pools_health.s())
    else:
        #c = check_pool_health.chunks(zip(args), 2).group()
        c = group(check_pool_health.s(pool) for pool in pools)
    return c()


@task
def check_pool_health(pool):
    logger.info("BLAH! pool=%s", pool)
    pool_name = pool.name
    pool_is_healthy = pool.is_healthy()
    if not pool_is_healthy:
        pool_health = pool.properties['health']
        logger.error("Storage pool '%s' has bad health='%s'!",
                     pool_name,
                     pool_health)
    return pool_is_healthy


"""
Auto Snapshot
"""

# TODO Get this from Web UI
config = {
    'schedules': {
        'testing': {
            # Schedule
            'snapshot-every':   timedelta( hours=1 ),
            # Creation
            'datasets':         ['dpool'], # TODO Select these from Web UI
            'snapshot-prefix':  'auto-testing-',
            'snapshot-date':    '%F_%T',
            # TODO Deletion code is not recursive friendly so this can currently NEVER be true
            'recursive':        False,
            # Removal
            'max-age': timedelta( days=7 ),
            'keep-at-most': 30,
        },
       'testing2': {
            # Schedule
            'snapshot-every':   timedelta( days=1 ),
            # Creation
            'datasets':         ['dpool'],
            'snapshot-prefix':  'auto-testing2-',
            'snapshot-date':    '%F_%T',
            # TODO Deletion code is not recursive friendly so this can currently NEVER be true
            'recursive':        False,
            # Removal
            'max-age': timedelta( days=7 ),
            'keep-at-most': 30,
        },
    },
}

class Auto_Snapshot( Task ):
#class Auto_Snapshot( PeriodicTask ):
    """ Cron job to periodically take a snapshot of datasets """
    #run_every = timedelta( minutes=5 )
    # TODO Make this work properly, maybe by populating config dict on the fly, until then don't run at all.
    abstract = True

    def run( self, *args, **kwargs ):
        # Get config and schedules
        schedules = config['schedules']
        for sched_name in schedules.keys():
            sched = schedules[sched_name]

            now = timezone.now()
            snapshotName = sched['snapshot-prefix'] + now.strftime( sched['snapshot-date'] )
            #logger.info('Snapshot %s for schedule %s', snapshotName, sched_name)
            #logger.debug('Schedule %s=%s', sched_name, sched)

            for dataset_name in sched['datasets']:
                try:
                    dataset = Filesystem.objects_including_disabled.get( name=dataset_name )
                except ( Filesystem.DoesNotExist ):
                    logger.error( "Was supposed to check if a snapshot was scheduled for dataset %s but it does not exist?", dataset_name )
                    continue

                try:
                    latest_snapshot_creation = dataset.snapshots().filter(
                        name__startswith=dataset_name + '@' + sched['snapshot-prefix'] ).latest().creation
                    age_threshold = now - sched['snapshot-every']
                    if not latest_snapshot_creation < age_threshold:
                        logger.info( "Latest snapshot for schedule %s dataset %s was taken at %s, no snapshot needed",
                                sched_name, dataset_name, latest_snapshot_creation )
                        continue
                except ( Snapshot.DoesNotExist ):
                    logger.info( "No latest snapshot found for %s, appears this will be our first", dataset )

                # Create snapshot
                # TODO Make seperate async task for this so we're not blocked
                logger.debug( "Creating snapshot %s on dataset %s", snapshotName, dataset_name )
                dataset.snapshot( snapshotName, recursive=sched['recursive'] )

                # Delete snapshots specified too old to keep
                # TODO Make seperate async task for this so we're not blocked
                # TODO Allow for recursive=True by querying Snapshot objects directly, not through dataset
                if 'max-age' in sched:
                    max_age = sched['max-age']
                    age_threshold = now - max_age

                    try:
                        snapshots_past_max_age = dataset.snapshots().filter(
                            name__startswith=dataset_name + '@' + sched['snapshot-prefix'],
                            creation__lt=age_threshold )
                    except ( Snapshot.DoesNotExist ):
                        logger.info( "No snapshots found past max age of %s", max_age )

                    if snapshots_past_max_age:
                        logger.info( 'Deleting snapshots created before %s: %s', age_threshold, snapshots_past_max_age )
                        for s in snapshots_past_max_age:
                            # Must do iterate through this or the overrode delete() will not be called
                            # To make this work without iterating, we must change to a pre_delete signal
                            #  instead of an overrode delete()
                            try:
                                s.delete()
                            except:
                                logger.error( "Failed to delete snapshot %s", s )

                # Keep X snapshots
                # TODO Make seperate async task for this so we're not blocked
                # TODO Allow for recursive=True by querying Snapshot objects directly, not through dataset
                if 'keep-at-most' in sched:
                    keep_at_most = sched['keep-at-most']

                    try:
                        snapshots_past_max_count = dataset.snapshots().filter(
                            name__startswith=dataset_name + '@' + sched['snapshot-prefix'] )[keep_at_most:]
                    except:
                        logger.info( "No snapshots found over keep-at-most count of %s", keep_at_most )

                    if snapshots_past_max_count:
                        logger.error( "Deleting snapshots past keep-at-most count of %s: %s",
                                keep_at_most, snapshots_past_max_count )
                        for s in snapshots_past_max_count:
                            try:
                                s.delete()
                            except:
                                logger.error( "Failed to delete snapshot %s", s )


#@task
#def Auto_Snapshot_Filesystem(*args, **kwargs):
#    """ Cleans up old automatic snapshots """
#    # TODO
#    pass

#@task
#def Auto_Snapshot_Filesystem_Clean(*args, **kwargs):
#    """ Cleans up old automatic snapshots """
#    # TODO
#    pass

