import logging
from django.db import models

class Config(models.Model):
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    def __unicode__(self):
        return self.key

class Pool(models.Model):
    name = models.CharField(max_length=128, unique=True)
    
    last_modified = models.DateTimeField(auto_now=True)
    delegation = models.BooleanField()
    listsnapshots = models.BooleanField()
    capacity = models.CharField(max_length=8)
    cachefile = models.CharField(max_length=255)
    free = models.CharField(max_length=32)
    ashift = models.IntegerField()
    autoreplace = models.BooleanField()
    bootfs = models.CharField(max_length=255)
    dedupditto = models.IntegerField()
    dedupratio = models.CharField(max_length=32)
    health = models.CharField(max_length=32)
    failmode = models.CharField(max_length=32)
    version = models.IntegerField()
    autoexpand = models.BooleanField()
    readonly = models.BooleanField()
    allocated = models.CharField(max_length=32)
    guid = models.CharField(max_length=32)
    altroot = models.CharField(max_length=255)
    size = models.CharField(max_length=32)
    def __unicode__(self):
        return self.name
    def dataset_filesystems(self, **kwargs):
        return self.dataset_set.filter(type='filesystem')

class Pool_IOStat(models.Model):
    pool = models.ForeignKey(Pool)
    timestamp = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    alloc = models.FloatField()
    free = models.FloatField()
    bandwidth_read = models.IntegerField()
    bandwidth_write = models.IntegerField()
    iops_read = models.IntegerField()
    iops_write = models.IntegerField()
    def __unicode__(self):
        return self.pool.name+'_'+self.timestamp.strftime('%F_%T')
    def timestamp_epoch(self):
        return self.timestamp.strftime('%s')

class Dataset(models.Model):
    name = models.CharField(max_length=128, unique=True)
    last_modified = models.DateTimeField(auto_now=True)
    basename = models.CharField(max_length=128)
    pool = models.ForeignKey(Pool)

    setuid = models.BooleanField()
    referenced = models.CharField(max_length=32)
    zoned = models.BooleanField()
    primarycache = models.CharField(max_length=32)
    logbias = models.CharField(max_length=32)
    creation = models.DateTimeField()
    sync = models.CharField(max_length=32)
    dedup = models.BooleanField()
    sharenfs = models.CharField(max_length=255)
    usedbyrefreservation = models.CharField(max_length=32)
    sharesmb = models.CharField(max_length=255)
    canmount = models.CharField(max_length=32)
    mountpoint = models.CharField(max_length=255)
    casesensitivity = models.CharField(max_length=32)
    utf8only = models.BooleanField()
    xattr = models.BooleanField()
    mounted = models.BooleanField()
    compression = models.CharField(max_length=32)
    usedbysnapshots = models.CharField(max_length=32)
    copies = models.IntegerField()
    aclinherit = models.CharField(max_length=32)
    compressratio = models.CharField(max_length=32)
    readonly = models.BooleanField()
    version = models.IntegerField() 
    normalization = models.CharField(max_length=32)
    type = models.CharField(max_length=32)
    secondarycache = models.CharField(max_length=32)
    refreservation = models.CharField(max_length=32)
    available = models.CharField(max_length=32)
    used = models.CharField(max_length=32)
    Exec = models.BooleanField()
    refquota = models.CharField(max_length=32)
    refcompressratio = models.CharField(max_length=32)
    quota = models.CharField(max_length=32)
    vscan = models.BooleanField()
    reservation = models.CharField(max_length=32)
    atime = models.BooleanField()
    recordsize = models.CharField(max_length=32)
    usedbychildren = models.CharField(max_length=32)
    usedbydataset = models.CharField(max_length=32)
    mlslabel = models.CharField(max_length=255)
    checksum = models.CharField(max_length=32)
    devices = models.BooleanField()
    nbmand = models.BooleanField()
    snapdir = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
    
    def snapshots(self, **kwargs):
        return dataset_snapshots(self.name, kwargs)
    
    def snapshot(self, **kwargs):
        """ Snapshot this dataset """
        logging.debug('Snapshot %s %s', self, kwargs)
        
        # Make the filesystem-level snapshot
        #TODO check retval
        try:
            zfs_snapshot(self.name, **kwargs)
            #TODO create database snapshot
            sync_zfs_db()
        except:
            print "nope"

#class Snapshot_Backup_Log(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    date = models.DateTimeField('log timestamp')
#    success = models.BooleanField()
#    description = models.CharField(max_length=255)

def dataset_snapshots(*datasets, **kwargs):
    dataset = datasets[0]
    try:
        datasets = Dataset.objects.filter(type='snapshot', name__startswith=dataset+'@')
    except (KeyError, Dataset.DoesNotExist):
        datasets = []
    return datasets

from solarsan.utils import zfs_snapshot
from cron import sync_zfs_db

## Schedule backups, snapshots, health status checks, etc
class Dataset_Cron(models.Model):
    name = models.CharField(max_length=128, unique=True)
    last_modified = models.DateTimeField(auto_now=True)

    dataset = models.ForeignKey(Dataset)
    recursive = models.BooleanField()

    task = models.CharField(max_length=128)
    schedule = models.CharField(max_length=128)




