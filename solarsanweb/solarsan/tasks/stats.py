from celery.task.base import PeriodicTask
from solarsan.models import Pool, Pool_IOStat
from solarsan.utils import convert_human_to_bytes
import logging
from datetime import timedelta
from django.utils import timezone
import zfs

class Pool_IOStats_Populate(PeriodicTask):
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


class Pool_IOStat_Clean(PeriodicTask):
    """ Periodic Task to clean old IOStats per pool in db """
    run_every = timedelta(days=1)
    def run(self, *args, **kwargs):
        delete_older_than = timedelta(days=180)
        count = Pool_IOStat.objects.all().count()

        try:
            count_to_remove = Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - delete_older_than).count()
        except (KeyError, Pool_IOStat.DoesNotExist):
            raise Exception("Cannot get list of entries to remove")

        if count_to_remove > 0:
            Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - delete_older_than).delete()

            logging.debug("Deleted %d/%d entires", count_to_remove, count)



