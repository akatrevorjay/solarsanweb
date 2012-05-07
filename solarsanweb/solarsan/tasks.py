from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes

from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot

from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask

import datetime
from datetime import timedelta
from django.utils import timezone
import time
import logging
from zfs import zfs


class CachedZFSPeriodicTask(PeriodicTask):
    """ Abstract template class that caches our ZFS object per worker """
    abstract = True


class Pool_IOStats_Populate(CachedZFSPeriodicTask):
    """ Periodic task to log iostats per pool to db. """
    run_every = timedelta(seconds=30)

    def run(self, capture_length=30, *args, **kwargs):
        iostats = zfs.Pools.iostat(capture_length=capture_length)
        timestamp_end = timezone.now()

        for i in iostats:
            ## Convert human readable values to bytes
            for j in ['alloc', 'free', 'bandwidth_read', 'bandwidth_write']:
                iostats[i][j] = int(convert_human_to_bytes(iostats[i][j]))

            try:
                pool = Pool.objects.get(name=i)
            except (KeyError, Pool.DoesNotExist):
                logging.error('Got data for an unknown pool "%s"', i)
                continue

            iostats[i]['timestamp_end'] = timestamp_end
            del iostats[i]['name']

            pool.pool_iostat_set.create(**iostats[i])
            return 0


class Pool_IOStat_Clean(CachedZFSPeriodicTask):
    """ Periodic Task to clean old IOStats per pool in db """
    run_every = timedelta(days=1)

    def run(self, *args, **kwargs):
        delete_older_than = timedelta(days=180)
        count = Pool_IOStat.objects.all().count()

        try:
            count_to_remove = Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - delete_older_than).count()
        except (KeyError, Pool_IOStat.DoesNotExist):
            logging.error("Cannot get list of entries to remove")
            return 0

        if count_to_remove > 0:
            Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - delete_older_than).delete()

            logging.debug("Deleted %d/%d entires", count_to_remove, count)

        return 0


class Auto_Snapshot(CachedZFSPeriodicTask):
    """ Cron job to periodically take a snapshot of datasets """
    #run_every = timedelta(minutes=1)
    run_every = timedelta(seconds=30)

    config = {
        'schedules': {
            'testing': {
                # Schedule
                'snapshot-every':   timedelta(seconds=30),
                # Creation
                'datasets':         ['rpool/tmp'],
                'snapshot-prefix':  'auto-testing-',
                'snapshot-date':    '%F_%T',
                # TODO Deletion code is not recursive friendly so this can currently NEVER be true
                'recursive':        False,
                # Removal
                'max-age': timedelta(days=7),
                'keep-at-most': 30,
            },
           'testing2': {
                # Schedule
                'snapshot-every':   timedelta(seconds=30),
                # Creation
                'datasets':         ['rpool/tmp'],
                'snapshot-prefix':  'auto-',
                'snapshot-date':    '%F_%T',
                # TODO Deletion code is not recursive friendly so this can currently NEVER be true
                'recursive':        False,
                # Removal
                'max-age': timedelta(days=7),
                'keep-at-most': 30,
            },
        },
    }

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        # Get config and schedules
        schedules = self.config['schedules']
        for sched_name in schedules.keys():
            sched = schedules[sched_name]

            now = timezone.now()
            snapshotName = sched['snapshot-prefix']+now.strftime(sched['snapshot-date'])
            logging.info('Snapshot %s for schedule %s', snapshotName, sched_name)
            logging.debug('Schedule %s=%s', sched_name, sched)

            for dataset_name in sched['datasets']:
                try:
                    dataset = Filesystem.objects.get(name=dataset_name)
                except (Filesystem.DoesNotExist):
                    logging.error("Was supposed to check if a snapshot was scheduled for dataset %s but it does not exist?", dataset_name)
                    continue

                try:
                    latest_snapshot_creation = dataset.snapshots().filter(
                        name__startswith=dataset_name+'@'+sched['snapshot-prefix'] ).latest().creation
                    age_threshold = now - sched['snapshot-every']
                    if not latest_snapshot_creation < age_threshold:
                        logging.info("Latest snapshot for schedule %s dataset %s was taken at %s, no snapshot needed",
                                sched_name, dataset_name, latest_snapshot_creation)
                        continue
                except (Snapshot.DoesNotExist):
                    logging.info("No latest snapshot found for %s, appears this will be our first", dataset)

                # Create snapshot
                # TODO Make seperate async task for this so we're not blocked
                logging.debug("Creating snapshot %s on dataset %s", snapshotName, dataset_name)
                dataset.snapshot(name=snapshotName, recursive=sched['recursive'])

                # Delete snapshots specified too old to keep
                # TODO Make seperate async task for this so we're not blocked
                # TODO Allow for recursive=True by querying Snapshot objects directly, not through dataset
                if 'max-age' in sched:
                    max_age = sched['max-age']
                    age_threshold = now - max_age

                    try:
                        snapshots_past_max_age = dataset.snapshots().filter(
                            name__startswith=dataset_name+'@'+sched['snapshot-prefix'],
                            creation__lt=age_threshold)
                    except (Snapshot.DoesNotExist):
                        logging.info("No snapshots found past max age of %s", max_age)

                    if snapshots_past_max_age:
                        logging.info('Deleting snapshots created before %s: %s', age_threshold, snapshots_past_max_age)
                        for s in snapshots_past_max_age:
                            # Must do iterate through this or the overrode delete() will not be called
                            # To make this work without iterating, we must change to a pre_delete signal
                            #  instead of an overrode delete()
                            try:
                                s.delete()
                            except:
                                logging.error("Failed to delete snapshot %s", s)

                # Keep X snapshots
                # TODO Make seperate async task for this so we're not blocked
                # TODO Allow for recursive=True by querying Snapshot objects directly, not through dataset
                if 'keep-at-most' in sched:
                    keep_at_most = sched['keep-at-most']

                    try:
                        snapshots_past_max_count = dataset.snapshots().filter(
                            name__startswith=dataset_name+'@'+sched['snapshot-prefix'])[keep_at_most:]
                    except:
                        logging.info("No snapshots found over keep-at-most count of %s", keep_at_most)

                    if snapshots_past_max_count:
                        logging.error("Deleting snapshots past keep-at-most count of %s: %s",
                                keep_at_most, snapshots_past_max_count)
                        for s in snapshots_past_max_count:
                            try:
                                s.delete()
                            except:
                                logging.error("Failed to delete snapshot %s", s)


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

class LocSol_Backup_Scheduler(CachedZFSPeriodicTask):
    """ Cron job to periodically backup configured dataset snapshots to LocSol """
    run_every = timedelta(seconds=60)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        for p in Pool.objects.all():
            d = p.dataset_set.get(name=p.name)
            logging.debug('LocSol_Backup on pool %s', p.name)

        return 0


# TODO This function should only be needed on initial deploys of solarsanweb and should not be a crutch
class Import_ZFS_Metadata(CachedZFSPeriodicTask):
    """ Syncs ZFS pools/datasets to DB """
    run_every = timedelta(minutes=5)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        # TODO Locking is requred here, although the copy offsets it a bit
        datasets = zfs.Datasets.copy()
        pools = zfs.Pools.copy()

        # Pools
        for p in pools:
            try:
                pool = Pool.objects.get(name=p)
                for k in pools[p]:
                    setattr(pool, k, pools[p][k])
            except (KeyError, Pool.DoesNotExist):
                logging.error('Found previously unknown pool "%s"', p)
                logging.debug('Pool: %s %s', p, pools[p])
                pool = Pool(**pools[p])

            pool.save()

        # Datasets
        for d in datasets:
            dataset = datasets[d]

            ## Remove unused args
            for k in ['parent', 'children']:
                if k in dataset:
                    del dataset[k]
            ## Rename exec to avoid pythonisms
            dataset['Exec'] = dataset['exec']
            del dataset['exec']

            time_format = "%a %b %d %H:%M %Y"
            dataset['creation'] = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dataset['creation'], time_format)))

            # Dataset
            if dataset['type'] == 'filesystem' or dataset['type'] == 'snapshot':
                try:
                    pool_dataset = Dataset.objects.get(name=d)
                    for k in dataset.keys():
                        setattr(pool_dataset, k, dataset[k])
                except (KeyError, Dataset.DoesNotExist):
                    logging.info('Found previously unknown %s "%s"', dataset['type'], d)
                    logging.debug('%s: %s %s', str(dataset['type']).capitalize(), d, dataset)

                    dataset_path = d.split('@')[0].split('/')
                    dataset_pool = Pool.objects.get(name=dataset_path[0])

                    pool_dataset = dataset_pool.dataset_set.create(**dataset)
                pool_dataset.save()

