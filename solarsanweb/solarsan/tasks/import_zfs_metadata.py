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
        datasets = zfs.dataset.list()
        pools = zfs.pool.list()

        # Pools
        for p,pv in pools.iteritems():
            try:
                pool = Pool.objects.get(name=p)
                for k,v in pv.iteritems():
                    setattr(pool, k, v)
            except (KeyError, Pool.DoesNotExist):
                logging.error('Found previously unknown pool "%s"', p)
                logging.debug('Pool: %s %s', p, pv)
                pool = Pool(**pv)
            pool.save()

        # Datasets
        for d,dv in datasets.iteritems():
            try:
                dataset = Dataset.objects.get(name=d)
                for k,v in dv.iteritems():
                    #print "p=%s k=%s v=%s" % (p, k, v)
                    setattr(dataset, k, v)
            except (KeyError, Dataset.DoesNotExist):
                logging.info('Found previously unknown %s "%s"', dv['type'], d)
                dataset_path = d.split('@')[0].split('/')
                dataset_pool = Pool.objects.get(name=dataset_path[0])
                dataset = dataset_pool.dataset_set.create(**dv)
            #print "dataset save"
            dataset.save(db_only=True, force_update=True)

        # Delete things which are no longer in existence
        for p in Pool.objects.all():
            if p.name not in pools.keys():
                logging.error("Pool '%s' is MISSING. Removing from DB.")
                #p.delete()
        for d in Dataset.objects.all():
            if d.name not in datasets.keys():
                logging.error("Dataset '%s' is MISSING. Removing from DB.")
                #d.delete()

