import kronos
import datetime, time
import logging
from solarsan.models import Pool, Pool_IOStat, Dataset
from solarsan.utils import zpool_iostat, zpool_list, zfs_list, convert_human_to_bytes, zfs_snapshot

from celery.schedules import crontab
from datetime import timedelta
from celery.task import periodic_task, task

@periodic_task(run_every=timedelta(seconds=30))
def cron_pool_iostats(*args, **kwargs):
    """ Cron job to periodically log iostats per pool to db.
        Also creates pools that do not exist in db """
    capture_length=30
    
    timestamp_start = datetime.datetime.now()
    iostats = zpool_iostat(capture_length, [])
    timestamp_end = datetime.datetime.now()
    
    for i in iostats:
        ## Convert human readable values to bytes
        for j in ['alloc', 'free', 'bandwidth_read', 'bandwidth_write']:
            iostats[i][j] = int(convert_human_to_bytes(iostats[i][j]))
        
        try:
            pool = Pool.objects.get(name=i)
        except (KeyError, Pool.DoesNotExist):
            logging.error('Got iostats for unknown pool "%s"', i)
            continue

        iostats[i]['timestamp'] = timestamp_start
        iostats[i]['timestamp_end'] = timestamp_end
        del iostats[i]['name']
        
        pool.pool_iostat_set.create(**iostats[i])

@periodic_task(run_every=crontab(minute="0", hour="0"))
def cron_pool_iostats_cleanup(*args, **kwargs):
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

@task
def cron_snapshot(*args, **kwargs):
    """ Cron job to periodically take a snapshot of datasets """
    
    for p in Pool.objects.all():
        d = p.dataset_set.get(name=p.name).snapshot(recursive=True)

@task
def sync_zfs_db(*args, **kwargs):
    """ Syncs ZFS pools/datasets to DB """
    
    datasets = zfs_list(type='all')
    pools = zpool_list()

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

