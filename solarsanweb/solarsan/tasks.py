## {{{ imports
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
from solarsan.models import Pool, Pool_IOStat, Dataset

from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask

import datetime
from datetime import timedelta
import time
import logging
import zfs
## }}}

## {{{ @abstract CachedZFSPeriodicTask
class CachedZFSPeriodicTask(PeriodicTask):
    """ Abstract template class that caches our ZFS object per worker """
    abstract = True
    _zfs = None

    @property
    def zfs(self):
        if self._zfs == None:
            self._zfs = zfs.zfs()
        return self._zfs
## }}}

## {{{ @30s Pool_IOStats_Populate
class Pool_IOStats_Populate(CachedZFSPeriodicTask):
    """ Periodic task to log iostats per pool to db. """
    run_every=timedelta(seconds=30)

    ## {{{ @30s run
    def run(self, *args, **kwargs):
        return self.populate(*args, **kwargs)
    ## }}}

    ## {{{ @daily Pool_IOStats_Clean
    #@periodic_task(run_every=timedelta(seconds=30))
    def populate(self, capture_length=30, *args, **kwargs):
        iostats = self.zfs.pool.iostat(capture_length)
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

    ## {{{ @daily Pool_IOStats_Clean
    #@periodic_task(run_every=timedelta(days=1))
    def clean(self, *args, **kwargs):
        """ Cron job to cleanup old iostat entries """

        delete_older_than = datetime.timedelta(days=180)
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
    ## }}}
## }}}

## {{{ @hourly LocSol_Backup_Begin
class LocSol_Backup_Begin(CachedZFSPeriodicTask):
    """ Cron job to periodically backup configured dataset snapshots to LocSol """
    run_every=timedelta(seconds=60)

    def run(self, *args, **kwargs):
        logging = self.get_logger()

        for p in Pool.objects.all():
            d = p.dataset_set.get(name=p.name)
            logging.debug('LocSol_Backup on pool %s', p.name)

        return 0
## }}}

## {{{ @minute Auto_Snapshot
class Auto_Snapshot(CachedZFSPeriodicTask):
    """ Cron job to periodically take a snapshot of datasets """
    run_every=timedelta(seconds=60)

    def __init__(self):
        self.config = {
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
        logging = self.get_logger()

        ## Get config and schedules
        schedules = self.config['schedules']
        for sched_name in schedules.keys():
            sched = schedules[sched_name]
            logging.debug("Schedule \"%s\"", sched_name)

            #str(sched['snapshot-prefix'])
            #for dataset in sched['datasets']:
                #d = p.dataset_set.get(name=p.name).snapshot(name=SnapshotName, recursive=True)

## }}}

## {{{ @daily Import_ZFS_Metadata ## TODO This function should only beneeded on initial deploys of solarsanweb and shoud not be a crutch
class Import_ZFS_Metadata(CachedZFSPeriodicTask):
    """ Syncs ZFS pools/datasets to DB """
    run_every=timedelta(days=1)

    def run(self, *args, **kwargs):
        datasets = self.zfs.dataset.list(type='all')
        pools = self.zfs.pool.list().keys()

        # Pools
        for p in pools:
            try:
                pool = Pool.objects.get(name=p)
                for k in pools[p]:
                    setattr(pool, k, pools[p][k])
            except (KeyError, Pool.DoesNotExist):
                logging.info('Found previously unknown pool "%s"', p)
                logging.debug('Pool: %s %s', p, pools[p])
                pool = Pool(**pools[p])

            pool.save()

        # Datasets (and snapshots)
        for d in datasets:
            dataset = datasets[d]
            
            ## Remove unused args
            for k in ['parent', 'children']:
                if dataset.has_key(k):
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
## }}}

