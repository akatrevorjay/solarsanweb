from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time, logging
from datetime import timedelta
from django.utils import timezone
#from django.core.files.storage import Storage

"""
Import pool/dataset info from system into DB
"""

import zfs

# TODO This function should only be needed on initial deploys of solarsanweb and should not be a crutch
class Import_ZFS_Metadata( PeriodicTask ):
    """ Syncs ZFS pools/datasets to DB """
    run_every = timedelta( minutes=5 )
    data = {}

    def run( self, *args, **kwargs ):
        logging = self.get_logger()
        self.data = {'pools': {}, 'datasets': {}}
        self.do_level( zfs.tree() )

        # Delete things which are no longer in existence
        for key, val in {'pools': Pool, 'datasets': Dataset}.items():
            # Do filter disabled ones from here!
            for obj in val.objects.all():
                if not obj.name in list( self.data[key] ):
                    logging.error( "Cannot find %s '%s' in ZFS, yet is in the DB. Disabling",
                            obj._zfs_type, obj.name )
                    obj.enabled = False
                    obj.save()
            self.data[key] = []

    def do_level( self, cur ):
        """ This gets called for each level of the tree to loop through it, then it's children """
        # First, take care of any objects
        if getattr( cur, 'has', None ):       self.do_level_items( cur )

        # Call this function recursively for each cur[key]
        for child_key in cur.keys():    self.do_level( cur[child_key] )

    def do_level_items( self, cur ):
        """ This gets called for each level of the tree to handle the level's items """
        has = getattr( cur, 'has', [] )

        # Pools
        if 'pools' in has:
            pools = cur.pools
            for pv in pools.itervalues():
                # The 'name' key of an object is always the full path name; ie, not relative to the tree.
                p = pv['name']
                try:
                    pool = Pool.objects_unfiltered.get( name=p )
                    pv['enabled'] = True
                    for k, v in pv.iteritems(): setattr( pool, k, v )
                except ( KeyError, Pool.DoesNotExist ):
                    logging.error( 'Found pool "%s"', p )
                    del pv['type']
                    pool = Pool( **pv )
                pool.save( db_only=True )
                self.data['pools'][p] = True

        # Datasets
        datasets = []
        if 'filesystems' in has: datasets.extend( cur.filesystems.items() )
        if 'snapshots' in has:   datasets.extend( cur.snapshots.items() )
        datasets = dict( datasets )
        for dv in datasets.values():
            # The 'name' key of an object is always the full path name; ie, not relative to the tree.
            d = dv['name']
            try:
                # Get existing dataset, if it doesn't exist the except below will catch it
                if dv['type'] == 'snapshot':        dataset = Snapshot.objects_unfiltered.get( name=d )
                elif dv['type'] == 'filesystem':    dataset = Filesystem.objects_unfiltered.get( name=d )
                elif dv['type'] == 'pool':          dataset = Pool.objects_unfiltered.get( name=d )
                else:
                    logging.error( "Found unknown type '%s': '%s'", dv['type'], d )
                    continue
                # Ensure enabled
                dv['enabled'] = True
                # Apply data to existing dataset
                for k, v in dv.iteritems(): setattr( dataset, k, v )
            except ( KeyError, Pool.DoesNotExist, Filesystem.DoesNotExist, Snapshot.DoesNotExist ):
                logging.info( 'Found %s "%s"', dv['type'], d )
                if dv['type'] == 'pool':
                    dataset = Pool( **dv )
                else:
                    dataset_path = d.split( '/' )
                    dataset_pool = Pool.objects_unfiltered.get( name=dataset_path[0].split( '@' )[0] )
                    dv['pool_id'] = dataset_pool.id
                    if dv['type'] == 'snapshot':
                        dataset = Snapshot( **dv )
                    elif dv['type'] == 'filesystem':
                        dataset = Filesystem( **dv )
            # Save dataset
            dataset.save( db_only=True )
            self.data['datasets'][d] = True


class Cleanup_Disabled_Storage_Items( PeriodicTask ):
    """ Cleans up disabled storage items from DB """
    run_every = timedelta( days=1 )
    def run( self, *args, **kwargs ):
        logging = self.get_logger()
        # Delete disabled items that are too old to care about.
        for key, val in {'pools': Pool, 'datasets': Dataset}.items():
            val.objects_unfiltered.filter( enabled=False, last_modified__gt=timezone.now() - timedelta( days=7 ) ).delete()


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

class Auto_Snapshot( PeriodicTask ):
    """ Cron job to periodically take a snapshot of datasets """
    run_every = timedelta( minutes=5 )
    # TODO Make this work properly, maybe by populating config dict on the fly, until then don't run at all.
    abstract = True

    def run( self, *args, **kwargs ):
        logging = self.get_logger( **kwargs )

        # Get config and schedules
        schedules = config['schedules']
        for sched_name in schedules.keys():
            sched = schedules[sched_name]

            now = timezone.now()
            snapshotName = sched['snapshot-prefix'] + now.strftime( sched['snapshot-date'] )
            #logging.info('Snapshot %s for schedule %s', snapshotName, sched_name)
            #logging.debug('Schedule %s=%s', sched_name, sched)

            for dataset_name in sched['datasets']:
                try:
                    dataset = Filesystem.objects.get( name=dataset_name )
                except ( Filesystem.DoesNotExist ):
                    logging.error( "Was supposed to check if a snapshot was scheduled for dataset %s but it does not exist?", dataset_name )
                    continue

                try:
                    latest_snapshot_creation = dataset.snapshots().filter( 
                        name__startswith=dataset_name + '@' + sched['snapshot-prefix'] ).latest().creation
                    age_threshold = now - sched['snapshot-every']
                    if not latest_snapshot_creation < age_threshold:
                        logging.info( "Latest snapshot for schedule %s dataset %s was taken at %s, no snapshot needed",
                                sched_name, dataset_name, latest_snapshot_creation )
                        continue
                except ( Snapshot.DoesNotExist ):
                    logging.info( "No latest snapshot found for %s, appears this will be our first", dataset )

                # Create snapshot
                # TODO Make seperate async task for this so we're not blocked
                logging.debug( "Creating snapshot %s on dataset %s", snapshotName, dataset_name )
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
                        logging.info( "No snapshots found past max age of %s", max_age )

                    if snapshots_past_max_age:
                        logging.info( 'Deleting snapshots created before %s: %s', age_threshold, snapshots_past_max_age )
                        for s in snapshots_past_max_age:
                            # Must do iterate through this or the overrode delete() will not be called
                            # To make this work without iterating, we must change to a pre_delete signal
                            #  instead of an overrode delete()
                            try:
                                s.delete()
                            except:
                                logging.error( "Failed to delete snapshot %s", s )

                # Keep X snapshots
                # TODO Make seperate async task for this so we're not blocked
                # TODO Allow for recursive=True by querying Snapshot objects directly, not through dataset
                if 'keep-at-most' in sched:
                    keep_at_most = sched['keep-at-most']

                    try:
                        snapshots_past_max_count = dataset.snapshots().filter( 
                            name__startswith=dataset_name + '@' + sched['snapshot-prefix'] )[keep_at_most:]
                    except:
                        logging.info( "No snapshots found over keep-at-most count of %s", keep_at_most )

                    if snapshots_past_max_count:
                        logging.error( "Deleting snapshots past keep-at-most count of %s: %s",
                                keep_at_most, snapshots_past_max_count )
                        for s in snapshots_past_max_count:
                            try:
                                s.delete()
                            except:
                                logging.error( "Failed to delete snapshot %s", s )


#@task
#def Auto_Snapshot_Filesystem(*args, **kwargs):
#    """ Cleans up old automatic snapshots """
#    #logging = self.get_logger(**kwargs)
#    # TODO
#    pass

#@task
#def Auto_Snapshot_Filesystem_Clean(*args, **kwargs):
#    """ Cleans up old automatic snapshots """
#    #logging = self.get_logger(**kwargs)
#    # TODO
#    pass
