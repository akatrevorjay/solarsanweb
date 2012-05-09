import logging
from django.db import models
import os, sys
import time, datetime, logging
from django.utils import timezone
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import FilterableDict
from solarsanweb.solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import zfs


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

    def filesystem(self):
        """ Returns the matching filesystem for Pool """
        return Filesystem.objects.get(pool_id=self.id, name=self.name)

    @property
    def zfs(self):
        """ Returns ZFS object for this dataset """
        zpool_list = zfs.zpool_list(self.name)
        return zpool_list[self.name]

    def delete(self, *args, **kwargs):
        """ Overridden delete that deletes the underlying ZFS object before deleting from DB """
        try:
            # Does the object exist in ZFS?
            zfs_pool = self.zfs
            zfs_existing = True
        except(Exception):
            logging.error("Was asked to delete ZFS pool '%s', but this pool does not exist in ZFS. "
                    + "Deleting from DB as it's not real anyway.", self.name)
            zfs_existing = False
        # If so, can we destroy it?
        if zfs_existing == True:
            try:
                #zfs.zfs_destroy(self.name)
                logging.error("DEBUG: NOT DELETING REGARDLESS OF WHAT YOU TELL ME")
            except:
                raise Exception("Failed to delete existing ZFS %s (%s), not deleting from DB",
                        zfs_pool['type'], self.name)
        # Delete from DB
        super(Pool, self).delete(*args, **kwargs)

    def filesystems(self, **kwargs):
        """ Lists filesystems of this pool """
        return Filesystem.objects.filter(type='filesystem', pool_id=self.id, **kwargs)

    def filesystem_create(self, name, **kwargs):
        """ Creates a filesystem in the pool """
        logging.info('Request to create filesystem (%s) on pool (%s)', name, self.name)
        # Get DB entry ready (and validate data)
        filesystem = Filesystem(name=name, pool_id=self.id)
        filesystem.save()
        # Return saved filesystem object
        return filesystem

    def iostat(self, **kwargs):
        """ Returns newly generated ZFS IOStats """
        zpool_iostat = zfs.zpool_iostat(self.name, **kwargs)
        return zpool_iostat[self.name]


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
        zfs_list = zfs.zfs_list(self.name)
        return zfs_list[self.name]

    def delete(self, *args, **kwargs):
        """ Overridden delete that deletes the underlying ZFS object before deleting from DB """
        try:
            # Does the object exist in ZFS?
            zfs_dataset = self.zfs
            zfs_existing = True
        except(Exception):
            logging.error("Was asked to delete ZFS dataset '%s', but this dataset does not exist in ZFS. "
                    + "Deleting from DB as it's not real anyway.", self.name)
            zfs_existing = False
        # If so, can we destroy it?
        if zfs_existing == True:
            try:
                #zfs.zfs_destroy(self.name)
                logging.error("DEBUG: NOT DELETING REGARDLESS OF WHAT YOU TELL ME")
            except:
                raise Exception("Failed to delete existing ZFS %s (%s), not deleting from DB",
                        self.type, self.name)
       # Delete from DB
        super(Dataset, self).delete(*args, **kwargs)


class Filesystem(Dataset):
    """ Filesystem """
    class Meta:
        proxy = True
    objects = FilesystemManager()

    def snapshots(self, **kwargs):
        """ Lists snapshots of this Filesystem """
        # Only filesystems can have snapshots
        return Snapshot.objects.filter(type='snapshot', name__startswith=self.name+'@', **kwargs)

    def snapshot(self, snapshot_name, **kwargs):
        """ Snapshot this dataset """
        logging.info('Snapshot %s on filesystem %s', snapshot_name, self.name)
        name = self.name+'@'+snapshot_name
        # Get DB entry ready (and validate data)
        snapshot = Snapshot(name=name, pool_id=self.pool_id)
        snapshot.save()
        # Return saved snapshot object
        return snapshot

    def save(self):
        """ Creates a filesystem and saves it to the DB """
        # Data validation should probably be done in zfs.zfs_create()
        # TODO Isn't there a transactional commit decorator?
        # Does filesystem exist already on filesystem?
        name = self.name
        try:
            # If it already exists, allow it through.
            zfs_ret = zfs.zfs_list(name)
            zfs_existing = True
            logging.info("While creating ZFS filesystem (%s), we've noticed it already exists in ZFS. "
                    + "Leaving filesystem as is, adding it to DB", name)
        except:
            # Good, it doesn't exist. Create it.
            zfs_ret = zfs.zfs_create(name)
            zfs_existing = False
            logging.info("Created ZFS filesystem (%s)", name)
        # Normalize data and stuff it into thyself
        try:
            for key,val in zfs_ret[name].iteritems():
                setattr(self, key, val)
            # Cool, now save to DB and hand it back
            super(Filesystem, self).save(self)
        except:
            if zfs_existing == False:
                zfs.zfs_destroy(self.name)
            raise Exception("Created ZFS filesystem but it could not be saved to DB. "
                    + "Destroying ZFS filesystem if it was created by this task")


class Snapshot(Dataset):
    """ Filesystem snapshot """
    class Meta:
        proxy = True
        ordering = ['-creation']
        get_latest_by = 'creation'
    objects = SnapshotManager()

    @property
    def snapshot_name(self):
        """ Returns the snapshot name """
        return self.basename.rsplit('@', 1)[1]

    @property
    def filesystem_name(self):
        """ Returns the associated filesystem name """
        return self.basename.rsplit('@', 1)[0]

    @property
    def filesystem(self):
        """ Returns the associated filesystem for this snapshot """
        return Filesystem.objects.get(name=self.filesystem_name)

    def save(self, **kwargs):
        """ Creates a filesystem snapshot and saves it to the DB """
        # Data validation should probably be done in zfs.zfs_snapshot()
        # TODO Isn't there a transactional commit decorator?
        # Does snapshot exist already on filesystem?
        name = self.name
        try:
            # If it already exists, allow it through.
            zfs_ret = zfs.zfs_list(name)
            zfs_existing = True
            logging.info("While creating ZFS snapshot (%s), we've noticed it already exists in ZFS. "
                    + "Leaving filesystem as is, adding it to DB", name)
        except:
            # Good, it doesn't exist. Create it.
            zfs_ret = zfs.zfs_snapshot(name)
            zfs_existing = False
        # Normalize data and stuff it into thyself
        try:
            for key,val in zfs_ret[name].iteritems():
                setattr(self, key, val)
            # Cool, now save to DB and hand it back
            super(Snapshot, self).save(self)
        except:
            if zfs_existing == False:
                zfs.zfs_destroy(self.name)
            raise Exception("Created ZFS snapshot but it could not be saved to DB. "
                    + "Destroying ZFS snapshot if it was created by this task")

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


