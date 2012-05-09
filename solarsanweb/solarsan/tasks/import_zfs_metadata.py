from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time, logging
from datetime import timedelta
from django.utils import timezone
import zfs

# TODO This function should only be needed on initial deploys of solarsanweb and should not be a crutch
class Import_ZFS_Metadata(PeriodicTask):
    """ Syncs ZFS pools/datasets to DB """
    run_every = timedelta(minutes=5)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        # TODO Locking is requred here, although the copy offsets it a bit
        datasets = zfs.zfs_list()
        pools = zfs.zpool_list()

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
            # TODO This will need a db_only=True kwarg when it's methods are overwritten
            pool.save()

        # Datasets
        for d in datasets:
            dataset = datasets[d]
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

