from celery import group
from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask, TaskSet
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from storage.models import Pool, Dataset, Filesystem, Volume, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
#from django.core.files.storage import Storage
from django.core.exceptions import ObjectDoesNotExist
#from django import db
#from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty
from solarsan.models import Config
import storage.target
import rtslib
import os
import logging
import sys

import time
from datetime import timedelta, datetime
from django.utils import timezone

##from django.core.files.storage import Storage
#from django.core.exceptions import ObjectDoesNotExist
##from django import db
##from django.db import import autocommit, commit, commit_manually, commit_on_success, is_dirty, is_managed, rollback, savepoint, set_clean, set_dirty

from . import signals


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


@task
def startup():
    signals.startup.send(sender=None)


def on_startup(**kwargs):
    logger.info("SolarSan Startup Signal! kwargs=%s", kwargs)

signals.startup.connect(on_startup)
