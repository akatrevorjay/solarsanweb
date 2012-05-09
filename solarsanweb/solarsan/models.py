import logging
from django.db import models
from zfs import zfs
import os, sys
import time, datetime, logging
from django.utils import timezone
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import FilterableDict
from solarsanweb.solarsan.utils import convert_bytes_to_human, convert_human_to_bytes

_paths = {'zfs':    "/usr/sbin/zfs",
          'zpool':  "/usr/sbin/zpool", }


class Config(models.Model):
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    def __unicode__(self):
        return self.key

#class PoolManager()

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
    guid = models.CharField(max_length=32, unique=True)
    altroot = models.CharField(max_length=255)
    size = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name

    def dataset(self):
        """ Returns the matching Dataset for Pool """
        return self.dataset_set.get(name=self.name)

# TODO Convert to/from bytes/human here, before handing it off
# TODO Can this be done with a Manager class instead?
#class zPools(Pool):

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


class FilesystemManager(models.Manager):
    def get_query_set(self):
        return super(FilesystemManager, self).get_query_set().filter(type='filesystem')

class SnapshotManager(models.Manager):
    def get_query_set(self):
        return super(SnapshotManager, self).get_query_set().filter(type='snapshot')

class Dataset(models.Model):
    class Meta:
        ordering = ['name', 'creation']

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

    @property
    def zfs(self):
        """ Returns ZFS object for this dataset """
        # TODO Swtch to zfs.Dataset(lookup=)
        return zfs.Datasets[self.name]

    def snapshots(self, **kwargs):
        """ Lists snapshots of this Filesystem """
        if self.type and self.type == 'snapshot':
            raise AttributeError
        return Snapshot.objects.filter(type='snapshot', name__startswith=self.name+'@', **kwargs)

    def snapshot(self, **kwargs):
        """ Snapshot this dataset """
        logging.info('Snapshot %s on filesystem %s', kwargs['name'], self.name)

        # Make the filesystem-level snapshot
        try:
            self.zfs.snapshot(**kwargs)
            #TODO create Snapshot and return it
            #HACK_Import_ZFS_Metadata.delay()
        except:
            logging.error('Snapshot %s %s failed', self, kwargs)

    def delete(self, *args, **kwargs):
        """ Overridden delete that deletes the underlying ZFS object before deleting from DB """
        try:
            from_db_only = kwargs.pop('from_db_only')
        except (KeyError):
            from_db_only = False

        if from_db_only == False:
            try:
                self.zfs.delete()
            except:
                if self.zfs:
                    logging.error("Failed to delete ZFS object for %s", self)
                    # TODO Better exceptions
                    #raise Exception
                else:
                    logging.error("Failed to delete ZFS object for %s because it doesn't exist?", self)
                    logging.error("CACHING PROBLEM")
                    #raise Exception
        super(Dataset, self).delete(*args, **kwargs)


class Filesystem(Dataset):
    class Meta:
        proxy = True
    objects = FilesystemManager()

class Snapshot(Dataset):
    class Meta:
        proxy = True
        ordering = ['-creation']
        get_latest_by = 'creation'
    objects = SnapshotManager()

    def filesystem(self):
        """ Returns the associated filesystem for this snapshot """
        #return self._base_manager.filter(type='filesystem', name=)
        pass
#    def pre_save(self, **kwargs):
    #def pre_delete(self, **kwargs):
    #    return False

#from solarsan.tasks import Import_ZFS_Metadata as HACK_Import_ZFS_Metadata


#class Snapshot_Backup_Log(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    date = models.DateTimeField('log timestamp')
#    success = models.BooleanField()
#    description = models.CharField(max_length=255)


## Schedule backups, snapshots, health status checks, etc
class Dataset_Cron(models.Model):
    name = models.CharField(max_length=128, unique=True)
    last_modified = models.DateTimeField(auto_now=True)

    dataset = models.ForeignKey(Dataset)
    recursive = models.BooleanField()

    task = models.CharField(max_length=128)
    schedule = models.CharField(max_length=128)


