from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time, logging
from datetime import timedelta
import zfs
import pyzfs

# TODO This function should only be needed on initial deploys of solarsanweb and should not be a crutch
class Import_ZFS_Metadata(PeriodicTask):
    """ Syncs ZFS pools/datasets to DB """
    run_every = timedelta(minutes=5)
    data = {}

    def run(self, *args, **kwargs):
        logging = self.get_logger()
        self.data = {'pools': {}, 'datasets': {}}
        self.do_level(zfs.tree.tree())

        # Delete things which are no longer in existence
        for key,val in {'pools': Pool, 'datasets': Dataset}.items():
            # Do filter disabled ones from here!
            for obj in val.objects.all():
                if not obj.name in list(self.data[key]):
                    logging.error("Cannot find %s '%s' in ZFS, yet is in the DB. Disabling",
                            obj._zfs_type, obj.name)
                    obj.enabled = False
                    obj.save()
            self.data[key] = []

    def do_level(self, cur):
        """ This gets called for each level of the tree to loop through it, then it's children """
        # First, take care of any objects
        if getattr(cur, 'has', None):       self.do_level_items(cur)

        # Call this function recursively for each cur[key]
        for child_key in cur.keys():    self.do_level(cur[child_key])

    def do_level_items(self, cur):
        """ This gets called for each level of the tree to handle the level's items """
        has = getattr(cur, 'has', [])

        # Pools
        if 'pools' in has:
            pools = cur.pools
            for pv in pools.itervalues():
                # The 'name' key of an object is always the full path name; ie, not relative to the tree.
                p = pv['name']
                try:
                    pool = Pool.objects_unfiltered.get(name=p)
                    pv['is_enabled'] = True
                    for k,v in pv.iteritems(): setattr(pool, k, v)
                except (KeyError, Pool.DoesNotExist):
                    logging.error('Found pool "%s"', p)
                    del pv['type']
                    pool = Pool(**pv)
                pool.save(db_only=True)
                self.data['pools'][p] = True

        # Datasets
        datasets = []
        if 'filesystems' in has: datasets.extend(cur.filesystems.items())
        if 'snapshots' in has:   datasets.extend(cur.snapshots.items())
        datasets = dict(datasets)
        for dv in datasets.values():
            # The 'name' key of an object is always the full path name; ie, not relative to the tree.
            d = dv['name']
            try:
                # Get existing dataset, if it doesn't exist the except below will catch it
                if dv['type'] == 'snapshot':        dataset = Snapshot.objects_unfiltered.get(name=d)
                elif dv['type'] == 'filesystem':    dataset = Filesystem.objects_unfiltered.get(name=d)
                elif dv['type'] == 'pool':          dataset = Pool.objects_unfiltered.get(name=d)
                else:
                    logging.error("Found unknown type '%s': '%s'", dv['type'], d)
                    continue
                # Ensure enabled
                dv['is_enabled'] = True
                # Apply data to existing dataset
                for k,v in dv.iteritems(): setattr(dataset, k, v)
            except (KeyError, Pool.DoesNotExist, Filesystem.DoesNotExist, Snapshot.DoesNotExist):
                logging.info('Found %s "%s"', dv['type'], d)
                if dv['type'] == 'pool':
                    dataset = Pool(**dv)
                else:
                    dataset_path = d.split('/')
                    dataset_pool = Pool.objects_unfiltered.get( name=dataset_path[0].split('@')[0] )
                    dv['pool_id'] = dataset_pool.id
                    if dv['type'] == 'snapshot':
                        dataset = Snapshot(**dv)
                    elif dv['type'] == 'filesystem':
                        dataset = Filesystem(**dv)
            # Save dataset
            dataset.save(db_only=True)
            self.data['datasets'][d] = True


