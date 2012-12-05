#from celery import subtask
from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask, TaskSet
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


#from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Volume, Snapshot
#from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
#import datetime, time
#from datetime import timedelta
#from django.utils import timezone
##from django.core.files.storage import Storage
#from django.core.exceptions import ObjectDoesNotExist
##from django import db
##from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty

#from django_mongokit import get_database, connection
#from configure.models import ClusterNode

"""
Reload tasks
"""
# This is wrong.
#from celery.app.control import broadcast

## TODO Automate this.
#class Celery_Reload(Task):
#    """ Reloads modules for all celery workers """
#    def run(self, *args, **kwargs):
#        broadcast('pool_restart', arguments={'reload': True})
