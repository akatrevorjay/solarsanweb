from django.db import models
from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import zfs

class EnabledModelManager(models.Manager):
    """ Returns objects that have enabled=True """
    def get_query_set(self):
        return super(EnabledModelManager, self).get_query_set().filter(enabled=True)

#class Snapshot_Backup_Log(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    date = models.DateTimeField('log timestamp')
#    success = models.BooleanField()
#    description = models.CharField(max_length=255)


## Schedule backups, snapshots, health status checks, etc
#class Cron(models.Model):
#    name = models.CharField(max_length=128, unique=True)
#    last_modified = models.DateTimeField(auto_now=True)
#    last_ret = models.IntegerField(default=0)
#    enabled = models.BooleanField(default=True)
#    run_every = models.IntegerField(default=0)
#    operate_on = models.CharField(max_length=128, default='')
#
#    task = models.CharField(max_length=128)
#    json = JSONField()
#
#    def __unicode__(self):
#        suffix = []
#        if not self.enabled: suffix.append("disabled")
#
#        if suffix: suffix = ' (' + ','.join(suffix) + ')'
#        else: suffix = ''
#        return '%s:%s%s' % (self.task, self.name, suffix)


