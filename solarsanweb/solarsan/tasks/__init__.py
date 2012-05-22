#from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
#from solarsan.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
#from celery.schedules import crontab
#from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
#import datetime, time, logging
#from datetime import timedelta
#from django.utils import timezone
#import zfs
from ZeroconfService import ZeroconfService

#class CachedZFSPeriodicTask(PeriodicTask):
#    """ Abstract template class that caches our ZFS object per worker """
#    abstract = True


class Console_ZeroConf_Control(Task):
    """ Controls console zeroconf services """
    service_console = ZeroconfService(name="SolarSan Console",
            port=80, stype="_demo._http")
    def run(self, action, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Performing action (%s) on console zeroconf services", action)

        if action == 'start':
            self.service_console.publish()
        if action == 'stop':
            self.service_console.unpublish()


#class SolarSan_Scheduler(Scheduler):
#    


