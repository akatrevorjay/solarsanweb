
import objects as zfs
import mongoengine
#from mongoengine import *

import logging
import datetime
import time



class Wrapper(object):
    cls = None
    obj = None
    obj_always = []
    def __init__(self, *args, **kwargs):
        if not getattr(self, 'cls'):
            raise Exception('No class was given to wrap')
        self.obj = self.cls(*args, **kwargs)
        super(Wrapper, self).__init__()
    def __getattr__(self, attr):
        # See if this object has attr; don't use hasattr unless you like loops.
        if attr in self.__dict__ and not attr in getattr(self, 'obj_always'):
            return getattr(self, attr)
        # Proxy
        return getattr(self.obj, attr)
    def proxy(self, attr):
        return getattr(self.obj, attr)





class zfsBaseDocument(mongoengine.Document):
    meta = {'abstract': True}
    name = mongoengine.StringField(required=True, unique=True)
    #name = mongoengine.StringField()
    enabled = mongoengine.BooleanField(default=True)
    # TODO Need to make this store as a dict in parent too
    #props = mongoengine.DictField()

    created = mongoengine.DateTimeField(default=datetime.datetime.now())
    modified = mongoengine.DateTimeField(default=datetime.datetime.now())

    def __init__(self, *args, **kwargs):
        # Apparently mongoengine.Document accepts no init *args
        super(zfsBaseDocument, self).__init__(**kwargs)


##
## Forget this, the mongo object should be wrapped, NOT the zfs object IMO.
##
## Maybe both should be wrapped, tbh.
##

class zfsBase(object):
    #meta = {'abstract': True}

    zfs = None
    db = None
    zfs_cls = None
    db_cls = zfsBaseDocument
    #zfs_always = []
    #db_always = []

    def __init__(self, *args, **kwargs):
        if not getattr(self, 'zfs_cls'):
            raise Exception('No class was given to wrap')

        if not 'name' in kwargs and args:
            if not isinstance(args, list):
                args = isinstance(args, basestring) and [args] or list(args)
            name = args.pop(0)
            kwargs['name'] = name

        self.zfs = self.zfs_cls(name)
        self.db, self.db_new = self.db_cls.objects.get_or_create(kwargs)

        super(zfsBase, self).__init__()

    def __repr__(self):
        return 'Solar%s' % self.zfs.__repr__()

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)

        for obj in [self.db, self.zfs]:
            if attr in obj.__dict__:
                return getattr(obj, attr)


class PoolDocument(zfsBaseDocument):
    pass

class DatasetDocument(zfsBaseDocument):
    pass

class FilesystemDocument(zfsBaseDocument):
    pass

class VolumeDocument(zfsBaseDocument):
    pass


class SnapshotDocument(zfsBaseDocument):
    pass


class Pool(zfsBase):
    meta = {'collection': 'storage_pools'}
    zfs_cls = zfs.Pool
    db_cls = PoolDocument

class Dataset(zfsBase):
    meta = {'collection': 'storage_datasets'}
    zfs_cls = zfs.Dataset
    db_cls = DatasetDocument


class Filesystem(zfsBase):
    meta = {'collection': 'storage_datasets'}
    zfs_cls = zfs.Filesystem
    db_cls = FilesystemDocument


class Volume(zfsBase):
    meta = {'collection': 'storage_datasets'}
    zfs_cls = zfs.Volume
    db_cls = VolumeDocument


class Snapshot(zfsBase):
    meta = {'collection': 'storage_datasets'}
    zfs_cls = zfs.Snapshot
    db_cls = SnapshotDocument



