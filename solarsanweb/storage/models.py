
from django.db import models
from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import zfs
import zfs.objects
import zfs.cmd

import datetime
from django.utils import timezone


"""
Mongo
"""

import mongoengine as m
from datetime import datetime

"""
Signal example

# Register signal
#import django.dispatch
#pizza_done = django.dispatch.Signal(providing_args=["toppings", "size"])

#class PizzaStore(object):
#    def send_pizza(self, toppings, size):
#    Both send() and send_robust() return a list of tuple pairs [(receiver, response), ... ], representing the list of called receiver functions and their response values.
#    send() differs from send_robust() in how exceptions raised by receiver functions are handled. send() does not catch any exceptions raised by receivers; it simply allows errors to propagate. Thus not all receivers may be notified of a signal in the face of an error.
#    send_robust() catches all errors derived from Python's Exception class, and ensures all receivers are notified of the signal. If an error occurs, the error instance is returned in the tuple pair for the receiver that raised the error.
#        pizza_done.send(sender=self, toppings=toppings, size=size)
#        pizza_done.send_robust(sender=self, toppings=toppings, size=size)

"""

# Start blank, add in defaults. At the bottom of this file customizations are done.
ZFS_TYPE_MAP = {}
ZFS_TYPE_MAP.update(zfs.objects.ZFS_TYPE_MAP)


class ReprMixIn(object):
    def __repr__(self):
        for k in ['name', 'guid', 'id']:
            name = getattr(self, k, None)
            if name:
                break
        return "<%s: %s>" % (self.__class__.__name__, name)
    def __unicode__(self):
        return self.name

class BaseMixIn(ReprMixIn):
    pass

#class BaseDocument(BaseMixIn, m.Document):
#    meta = {'abstract': True,}


"""
Property
"""

class PropertyDocument(BaseMixIn, m.EmbeddedDocument):
    meta = {'abstract': True, }
    name = m.StringField(required=True, unique=True)
    value = m.StringField()

    #created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    #modified = m.DateTimeField(default=datetime.now())

class Property(PropertyDocument):
    pass


"""
Base
"""

class zfsBaseDocument(BaseMixIn, m.Document):
    meta = {'abstract': True,
            'ordering': ['-created']}
    name = m.StringField(required=True, unique=True)
    #type = m.StringField(required=True)
    #name = m.StringField()
    # TODO Need to make this store as a dict in parent too
    props = m.MapField(m.EmbeddedDocumentField(Property))
    #misc = m.DictField()
    importing = m.BooleanField()

    created = m.DateTimeField(default=datetime.now())
    # TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())
    enabled = m.BooleanField()

    def __init__(self, *args, **kwargs):
        # Apparently m.Document accepts no init *args
        # for cls in self.
        #BaseMixIn.__init__()
        return super(zfsBaseDocument, self).__init__(**kwargs)

class zfsBase(zfs.objects.zfsBase):
    ZFS_TYPE_MAP = ZFS_TYPE_MAP

    def exists(self, force_check=False):
        """
        Checks if object exists.
        If force_check=True, don't assume existence if object is in DB; always check on the filesystem level.
        """
        if not force_check and getattr(self, 'id', None):
            return True
        else:
            return super(zfsBase, self).exists()
            #return zfs.objects.zfsBase.exists(self)

    #@classmethod
    #def _list_class(self, *args, **kwargs):
    #    ######################################
    #    #### FUCKIN HACKERY DONT DO THIS #####
    #    ######################################
    #    ret = super(zfsBase, self).list(*args, **kwargs)
    #    if ret:
    #        if isinstance(ret, list):
    #            for v in ret:
    #                if getattr(v, 'reload'):
    #                    v.reload()
    #    return ret
    #    return zfs.objects.zfsBase.exists(self)

"""
VDevs
"""

class VDevBaseDocument(BaseMixIn, m.EmbeddedDocument):
    meta = {'abstract': True, }
            #'ordering': ['-created']}

    #VDEV_TYPES=['root', 'mirror', 'disk']
    #type = m.StringField(required=True, choices=VDEV_TYPES)
    #vdev_id = m.IntField(unique=True, primary_key=True)
    vdev_id = m.IntField()
    guid = m.StringField(unique=True)

    created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())

class VDevRootDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    #pool_guid = m.StringField()
    #vdev_id = m.IntField()
    state = m.IntField()
    txg = m.IntField()

class VDevRoot(VDevRootDocument):
    pass



class VDevPoolDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    version = m.IntField()
    name = m.StringField()
    state = m.IntField()
    txg = m.IntField()
    hostname = m.StringField()

    vdev_children = m.IntField()
    vdev_tree = m.MapField(m.EmbeddedDocumentField(VDevRoot))

class VDevPool(VDevPoolDocument):
    #def children(self):
    #    pass
    pass



class VDevChildDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    ashift = m.IntField()
    asize = m.IntField()
    create_txg = m.IntField()
    # Only on mirrored vdevs
    DTL = m.IntField()
    resilvering = m.IntField()
    is_log = m.IntField()
    metaslab_array = m.IntField()
    metaslab_shift = m.IntField()

class VDevDiskDocument(VDevChildDocument):
    meta = {'abstract': True, }
    path = m.StringField()
    whole_disk = m.IntField()

class VDevDisk(VDevDiskDocument):
    pass

class VDevMirrorDocument(VDevChildDocument):
    meta = {'abstract': True, }
    children = m.ListField(m.EmbeddedDocumentField(VDevDisk))

class VDevMirror(VDevMirrorDocument):
    pass


VDEV_TYPE_MAP = {'root': None,
                 'mirror': VDevMirror,
                 'disk': VDevDisk, }


"""
Pool
"""

class PoolDocument(zfsBaseDocument):
    meta = {'collection': 'pools',
            'abstract': True, }
    version = m.IntField()
    state = m.IntField()
    txg = m.IntField()
    #guid = m.StringField(unique=True, required=True, primary_key=True)
    guid = m.StringField(unique=True)
    hostname = m.StringField()
    vdevs = m.ListField(m.EmbeddedDocumentField(VDevChildDocument))

    VDEV_TYPE_MAP = VDEV_TYPE_MAP

    @property
    def filesystem(self):
        """ Returns the matching Filesystem for this Pool """
        assert self.name, "Cannot get filesystem for unnamed Pool"
        #obj, created = self.ZFS_TYPE_MAP['filesystem'].objects.get_or_create(name=self.name, pool=self)
        obj, created = self.ZFS_TYPE_MAP['filesystem'].objects.get_or_create(name=self.name, pool=self, auto_save=False)
        if created:
            obj.guid = obj.get('guid')['value']
            obj.save()
        return obj

    def filesystems(self):
        return Filesystem.objects.filter(pool=self)

    def reload_zdb(self):
        """ Snags pool status and vdev info from zdb as zpool status kind of sucks """
        z = zfs.cmd.ZdbCommand('-C', '-v')
        ret = z(ofilter=zfs.cmd.SafeYamlFilter)
        ret = ret[self.name]
        self._parse_zdb(ret)

    def _parse_zdb(self, ret):
        """ Parses pool status and vdev info from given zdb data """
        # Basic info
        # hostname, vdev_children, vdev_tree, name(single quoted)
        self.guid = unicode(ret['pool_guid'])
        self.state = ret['state']
        self.txg = ret['txg']
        self.version = ret['version']

        # Just a count
        vdev_children = ret['vdev_children']

        # VDev parser
        self._parse_zdb_vdev_tree(ret['vdev_tree'])

    def _parse_zdb_vdev_tree(self, cur):

        def parse_vdev(cls, data):
            obj = {}
            data['vdev_id'] = data.pop('id', None)
            for v in cls._fields.keys():
                if v == 'id':
                    continue
                if v in data:
                    obj[v] = unicode(data[v])
            return cls(**obj)

        obj_type = cur['type']
        obj_cls = self.VDEV_TYPE_MAP[obj_type]
        if obj_cls:
            obj = parse_vdev(obj_cls, cur)
        else:
            obj = None
        children = []

        # Don't look for children with a type of disk, cause disks don't let disks have disks
        if obj_type in ['mirror', 'root']:
            # Walk through recursively
            for v in cur.itervalues():
                if isinstance(v, dict):
                    cobj = self._parse_zdb_vdev_tree(cur=v)
                    children.append(cobj)
                    #children.insert(cobj.id, cobj)

        if obj:
            obj.children = children
            return obj
        elif obj_type == 'root':
            self.vdevs = children
        else:
            raise Exception("Could not parse VDev tree")

class Pool(PoolDocument, zfs.objects.PoolBase, zfsBase):
    pass

"""
PoolIOStat
"""

# TODO Get rid of this once and for all, use cube instead
class PoolIOStatDocument(m.Document, BaseMixIn):
    meta = {'abstract': True, }
            #'collection': 'pool_io_stat', }
    pool = m.ReferenceField(Pool)

    timestamp = m.DateTimeField()
    timestamp_end = m.DateTimeField()

    alloc = m.FloatField()
    free = m.FloatField()
    bandwidth_read = m.IntField()
    bandwidth_write = m.IntField()
    iops_read = m.IntField()
    iops_write = m.IntField()

    def __unicode__( self ):
        return self.pool.name + '_' + self.timestamp.strftime('%F_%T')

class PoolIOStat(PoolIOStatDocument):
    def timestamp_epoch( self ):
        return self.timestamp.strftime('%s')


# Old alias, temporary cause I'm lazy
Pool_IOStat = PoolIOStat



"""
Dataset
"""


class DatasetDocument(zfsBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True, }
            #'abstract': True, }
    pool = m.ReferenceField(Pool,
                            reverse_delete_rule=m.CASCADE)
    parent = m.GenericReferenceField()
    #parent = m.ReferenceField(DatasetDocument,
    #                          reverse_delete_rule=m.CASCADE)
    guid = m.StringField(unique=True)

    #def __init__(self, *args, **kwargs):
    #    return super(DatasetDocument, self).__init__(*args, **kwargs)

    #def children(self, **kwargs):
    #    return super(DatasetDocument, self).children(**kwargs)

class DatasetBase(zfs.objects.DatasetBase):
    pass

class Dataset(DatasetDocument, DatasetBase, zfsBase):
    pass

class SnapshottableDatasetBase(zfs.objects.SnapshottableDatasetBase):
    def filesystems(self):
        return Filesystem.objects.filter(pool=self.pool, name__startswith='%s/' % self.name)

    def snapshots(self):
        return Snapshot.objects.filter(pool=self.pool, name__startswith='%s/' % self.name)


class FilesystemDocument(DatasetDocument):
    #meta = {'abstract': True,}
    pass

class FilesystemBase(zfs.objects.FilesystemBase):
    pass

class Filesystem(FilesystemDocument, FilesystemBase, SnapshottableDatasetBase, DatasetBase, zfsBase):
#class Filesystem(FilesystemBase, SnapshottableDatasetBase, DatasetBase, zfsBase, FilesystemDocument):
    pass

#class Filesystem(FilesystemDocument, SnapshottableDatasetBase, zfs.objects.FilesystemBase, DatasetBase, zfsBase):
#    pass



class VolumeDocument(DatasetDocument):
    #meta = {'abstract': True,}
    pass

class Volume(VolumeDocument, SnapshottableDatasetBase, zfs.objects.VolumeBase, DatasetBase, zfsBase):
    pass



class SnapshotDocument(DatasetDocument):
    #meta = {'abstract': True,}
    pass

class Snapshot(SnapshotDocument, zfs.objects.SnapshotBase, DatasetBase, zfsBase):
    pass


"""
ZFS Object Map
"""

ZFS_TYPE_MAP.update({
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    #'properties': zfs.objects.Properties,
})
