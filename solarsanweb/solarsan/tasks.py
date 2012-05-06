from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes

from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot

from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask

import datetime
from datetime import timedelta
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
        timestamp_end = datetime.datetime.now()

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
            count_to_remove = Pool_IOStat.objects.filter(timestamp_end__lt=datetime.datetime.now() - delete_older_than).count()
        except (KeyError, Pool_IOStat.DoesNotExist):
            logging.error("Cannot get list of entries to remove")
            return 0

        if count_to_remove > 0:
            Pool_IOStat.objects.filter(timestamp_end__lt=datetime.datetime.now() - delete_older_than).delete()

            logging.debug("Deleted %d/%d entires", count_to_remove, count)

        return 0

class Auto_Snapshot(CachedZFSPeriodicTask):
    """ Cron job to periodically take a snapshot of datasets """
    run_every = timedelta(days=1)

    config = {
        'schedules': {
            'testing': {
                ## Schedule
                'snapshot-every':   timedelta(seconds=30),
                'remove-every':     timedelta(seconds=30),

                ## Creation
                'datasets':         ['rpool/tmp'],
                #'datasets-all':    True,
                'snapshot-prefix':  'auto-testing-%F_%T',
                'recursive':        False,

                ## Removal
                'snapshot-max-age': timedelta(minutes=5),
            },
        },
    }

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        # Get config and schedules
        schedules = self.config['schedules']
        for sched_name in schedules.keys():
            sched = schedules[sched_name]

            snapshotName = datetime.datetime.now().strftime(sched['snapshot-prefix'])
            logging.info('Snapshot %s for schedule "%s"', snapshotName, sched_name)
            logging.debug('Schedule "%s"=%s', sched_name, sched)

            for dataset_name in sched['datasets']:
                try:
                    dataset = Filesystem.objects.get(name=dataset_name)
                except (Dataset.DoesNotExist):
                    logging.error("Was supposed to snapshot dataset %s but it does not exist?", dataset_name)
                    continue

                # TODO Make seperate async task for this so we're not blocked
                logging.debug("Creating snapshot %s on dataset %s", snapshotName, dataset_name)
                dataset.snapshot(name=snapshotName, recursive=sched['recursive'])
                # TODO Clean up old snaps

@task
def Auto_Snapshot_Filesystem(*args, **kwargs):
    """ Cleans up old automatic snapshots """
    logging = self.get_logger(**kwargs)
    # TODO

@task
def Auto_Snapshot_Filesystem_Clean(*args, **kwargs):
    """ Cleans up old automatic snapshots """
    logging = self.get_logger(**kwargs)
    # TODO


class LocSol_Backup_Scheduler(CachedZFSPeriodicTask):
    """ Cron job to periodically backup configured dataset snapshots to LocSol """
    run_every = timedelta(seconds=60)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        for p in Pool.objects.all():
            d = p.dataset_set.get(name=p.name)
            logging.debug('LocSol_Backup on pool %s', p.name)

        return 0


## TODO This function should only beneeded on initial deploys of solarsanweb and should not be a crutch
class Import_ZFS_Metadata(CachedZFSPeriodicTask):
    """ Syncs ZFS pools/datasets to DB """
    run_every = timedelta(minutes=1)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        datasets = zfs.Datasets
        pools = zfs.Pools

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

