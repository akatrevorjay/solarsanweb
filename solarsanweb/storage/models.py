from django.db import models
from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import zfs

from solarsan.models import EnabledModelManager

class ZFSBackedModel(models.Model):
    class Meta:
        abstract = True
    _zfs_type = None
    enabled = models.BooleanField(default=True)
    objects = EnabledModelManager()
    objects_unfiltered = models.Manager()

    def save(self, **kwargs):
        """ Creates a (self._zfs_type) and saves it to the DB """
        # If we're importing, just save directly
        if kwargs.pop('db_only', False) == True or self.pk:
            return super(ZFSBackedModel, self).save()

        # If we get here, we're not importing.
        zfs_type = self._zfs_type

        # Does filesystem exist already on filesystem?
        name = self.name
        try:
            # If it already exists, allow it through.
            if zfs_type in ['filesystem', 'snapshot', 'dataset']:
                zfs_ret = zfs.dataset.list(name)
            elif zfs_type in ['pool']:
                zfs_ret = zfs.pool.list(name)
            else:
                raise Exception("Object to be saved has an invalid type '%s'" % zfs_type)
            zfs_existing = True
            logging.info("While creating requested " + zfs_type
                    + " '%s', we've noticed it already exists in ZFS. Leaving " + zfs_type
                    + " as is in ZFS; Saving to DB", name, name)
        except:
            # Good, it doesn't exist. Create it.
            if zfs_type == 'snapshot':
                zfs_ret = zfs.dataset.snapshot(name)
            elif zfs_type in ['filesystem', 'dataset']: # Should really just stop using Dataset.
                zfs_ret = zfs.dataset.create(name)
            elif zfs_type == 'pool':
                # FIXME NOT IMPLEMENTED YET
                zfs_ret = zfs.pool.create(name)
            else:
                raise Exception("This " + zfs_type + " has an incorrect zfs_type, no thanks")
            zfs_existing = False
            logging.info("Created " + zfs_type + " in ZFS '%s', saving in DB", name)

        try:
            # Normalize data and stuff it
            for key,val in zfs_ret[name].iteritems():
                # I'm paranoid
                if key == '_zfs_type': continue
                setattr(self, key, val)

            # Cool, now save to DB and hand it back
            super(ZFSBackedModel, self).save()
        except:
            # Since we're failing out due to something not going right with the DB save,
            #   If the zfs object was NOT previously existing, ie this function actually created it,
            #   then destroy it.
            if zfs_existing == False:
                # FIXME POOL OR DATASET DIFF CMDS
                zfs.dataset.destroy(self.name)
                logging.error("Destroyed %s '%s' in ZFS since we're erroring out.", zfs_type, name)
            raise Exception("Created " + zfs_type + " in ZFS but it could not be saved to DB. ")

    def delete(self, *args, **kwargs):
        """ Overridden delete that deletes the underlying ZFS object before deleting from DB """
        # If we're importing, just save directly
        if kwargs.pop('db_only', False) == True:
            return super(ZFSBackedModel, self).delete(*args, **kwargs)

        ## If we do not have a _zfs_type attribute, we may want to push it through to the DB
        #try:
        zfs_type = self._zfs_type
        name = self.name
        #except:
        #    super(ZFSBackedModel, self).save(self)

        # Does the object exist in ZFS? 
        try:
            zfs_ret = zfs.dataset.list(name)
            zfs_existing = True
        except(Exception):
            zfs_existing = False

        # If so, can we destroy it?
        if zfs_existing == True:
            try:
                logging.info("Destroying %s '%s' [existing=%s]", zfs_type, name, zfs_existing)
                zfs.dataset.destroy(name)
            except:
                raise Exception("Failed to delete existing " + zfs_type + " in ZFS '%s', not deleting from DB", name)
        # Delete from DB
        super(ZFSBackedModel, self).delete(*args, **kwargs)

    def path(self, start=0, len=None):
        """ Splits name of object into paths starting at index start """
        return self.name.split('/')[start:len]


class Pool(ZFSBackedModel):
    _zfs_type = 'pool'
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

    @property
    def zfs(self):
        """ Returns ZFS object for this dataset """
        zpool_list = zfs.pool.list(self.name)
        return zpool_list[self.name]

    @property
    def filesystem(self):
        """ Returns the matching filesystem for Pool """
        return Filesystem.objects.get(pool_id=self.id, name=self.name)

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
        zpool_iostat = zfs.pool.iostat(self.name, **kwargs)
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
        return self.pool.name + '_' + self.timestamp.strftime('%F_%T')

    def timestamp_epoch(self):
        return self.timestamp.strftime('%s')


class FilesystemManager(models.Manager):
    def get_query_set(self):
        return super(FilesystemManager, self).get_query_set().filter(type='filesystem', enabled=True)


class SnapshotManager(models.Manager):
    def get_query_set(self):
        return super(SnapshotManager, self).get_query_set().filter(type='snapshot', enabled=True)


class Dataset(ZFSBackedModel):
    class Meta:
        ordering = ['name', 'creation']
    _zfs_type = 'dataset'

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
        zfs_list = zfs.dataset.list(self.name)
        return zfs_list[self.name]


class Filesystem(Dataset):
    """ Filesystem """
    class Meta:
        proxy = True
    _zfs_type='filesystem'
    objects = FilesystemManager()

    def snapshots(self, **kwargs):
        """ Lists snapshots of this filesystem """
        # Only filesystems can have snapshots
        return Snapshot.objects.filter(type='snapshot', name__startswith=self.name + '@', **kwargs)

    def snapshot(self, snapshot_name, **kwargs):
        """ Snapshot this filesystem """
        logging.info('Snapshot %s on filesystem %s', snapshot_name, self.name)
        name = self.name + '@' + snapshot_name
        # Get DB entry ready (and validate data)
        snapshot = Snapshot(name=name, pool_id=self.pool_id)
        snapshot.save()
        # Return saved snapshot object
        return snapshot


class Snapshot(Dataset):
    """ Filesystem snapshot """
    _zfs_type='snapshot'
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


