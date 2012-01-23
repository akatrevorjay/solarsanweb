from django.db import models
import datetime

class Config(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    def __unicode__(self):
        return self.key

class Pool(models.Model):
    name = models.CharField(max_length=128)
    def __unicode__(self):
        return self.name

class Pool_IOStat(models.Model):
    pool = models.ForeignKey(Pool)
    timestamp = models.DateTimeField()
    alloc = models.IntegerField()
    free = models.IntegerField()
    bandwidth_read = models.IntegerField()
    bandwidth_write = models.IntegerField()
    iops_read = models.IntegerField()
    iops_write = models.IntegerField()
    def __unicode__(self):
        return self.pool.name+'_'+self.timestamp.strftime('%F_%T')

#class Dataset(models.Model):
#    dataset = models.CharField(max_length=128)
#    pool = models.ForeignKey(Pool)

#class Snapshot(models.Model):
#    dataset = models.CharField(max_length=128)

#class Snapshot_Backup_Log(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    date = models.DateTimeField('log timestamp')
#    success = models.BooleanField()
#    description = models.CharField(max_length=255)
