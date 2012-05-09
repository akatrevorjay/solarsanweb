from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time, logging
from datetime import timedelta
from django.utils import timezone
import zfs


class LocSol_Backup_Scheduler(PeriodicTask):
    """ Cron job to periodically backup configured dataset snapshots to LocSol """
    run_every = timedelta(seconds=60)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        for p in Pool.objects.all():
            d = p.dataset_set.get(name=p.name)
            logging.debug('LocSol_Backup on pool %s', p.name)

        return 0


