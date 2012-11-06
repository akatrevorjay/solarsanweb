
from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.utils.log import get_task_logger
from celery.task.sets import subtask
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
Import pool/dataset info from system into DB
"""


class Import_ZFS_Metadata(PeriodicTask):
    run_every = timedelta(minutes=30)

    def run(self, *args, **kwargs):
        for pool in Pool.list(ret=list):
            pool_name = pool.name
            if not getattr(pool, 'id', None):
                logger.warning("Found new ZFS storage pool '%s'", pool_name)
            pool.reload_zdb()
            pool.save()

            if not pool.health_check():
                pool_health = pool.properties['health']
                logger.error("Can't import storage pool '%s' as it has bad health='%s'!",
                             pool_name,
                             pool_health)
                continue

            pool_fs = pool.filesystem

            for v in [Filesystem, Volume, Snapshot]:
                if not getattr(v, 'objects', None):
                    continue
                v.objects.filter(name__startswith='%s/' % pool_name).update(set__importing=True, multi=True)
                v.objects.filter(name__startswith='%s@' % pool_name).update(set__importing=True, multi=True)

            pool_fs.list(args=['-r', pool_name], type='all')

            for v in [Filesystem, Volume, Snapshot]:
                if not getattr(v, 'objects', None):
                    continue
                #v.objects.filter(importing=True, enabled__ne=False).update(set__enabled=False)
                #v.objects.filter(importing=True).delete(modified__lt=timezone.now() -
                #                                        datetime.timedelta(days=7))
                v.objects.filter(importing=True).delete()



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
                    dataset = Filesystem.objects.get( name=dataset_name )
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

