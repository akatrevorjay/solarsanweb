
import zfs.objects as zfs
import mongoengine
#from mongoengine import *

import logging
import datetime
import time


class TimestampedDocument(mongoengine.Document):
    meta = {'abstract': True,
            'allow_inheritance': True,
            }
    created = mongoengine.DateTimeField(default=datetime.datetime.now())
    modified = mongoengine.DateTimeField(default=datetime.datetime.now())


##class Property(mongoengine.EmbeddedDocument, zfs.Property):
#class Property(mongoengine.EmbeddedDocument):
#    meta = {'abstract': True,
#            }
#    name = mongoengine.StringField(required=True)
#    value = mongoengine.StringField(required=True)
#    source = mongoengine.StringField()
#
#    def __str__(self):
#        return str(self.value)
#    def __unicode__(self):
#        return unicode(self.value)
#    def __repr__(self):
#        return "Property(name=%s, value=%s, source=%s)" % (self.name, self.value, self.source)
#    def __call__(self, *args, **kwargs):
#        """ Sets property with value """
#        #if hasattr(self, 'parent'): self.parent.set(self.name, value)
#        return super(Property, self).__call__(*args, **kwargs)


class zfsBaseMongo(TimestampedDocument):
    meta = {'abstract': True,
            'allow_inheritance': True,
            'indexes': [{'fields': ['name'], 'unique': True}],
            }
    name = mongoengine.StringField(required=True, unique=True)
    enabled = mongoengine.BooleanField(default=True)
    # TODO Need to make this store as a dict in parent too
    #props = mongoengine.DictField()


class zfsBase(zfs.zfsBase, zfsBaseMongo):
    ##
    ## TODO Figure out how to handle the procedure of ensuring proper order
    ##   of events has happened, ie do not save in db if it's not yet created,
    ##   etc
    ##
    pass

    #def get(self, *args, **kwargs):
    #    # With a Mongo backend, the props for self are stored in the document for the parent object.
    #    pass
    #
    #    # We may want to resort to going direct in certain cases however, so keeping this here until we may.
    #    #return super(zfsBaseMongo, self).get(*args, **kwargs)

    #def zfs(self):
    #    """ Backwards compat, but I doubt this will be needed """
    #    return self



class PoolMongo(zfsBaseMongo):
    meta = {'collection': 'storage_pools',
            }
    #filesystem = mongoengine.ReferenceField(Filesystem, reverse_delete_rule=CASCADE)



class Pool(zfs.Pool, PoolMongo):
    pass

    ##
    ## TODO Should this be overriden to return db data or should the mongo object's attrs return db data,
    ##   but whenever list() or get() are called, it automatically updates those objects?
    ##

    #def list(self, *args, **kwargs):
    #    super(Pool, self).list(*args, **kwargs)

    #def get(self, *args, **kwargs):
    #    super(Pool, self).list(*args, **kwargs)


class DatasetMongo(zfsBaseMongo):
    meta = {'collection': 'storage_datasets',
            }
    #pool = mongoengine.ReferenceField(Pool, reverse_delete_rule=CASCADE)


class Dataset(zfs.Dataset, DatasetMongo):
    pass

    #def __init__(self, name, *args, **kwargs):
    #    super(Dataset, self).__init__(name, *args, **kwargs)

    #def __new__(cls, *args, **kwargs):
    #    if 'type' in kwargs:
    #        for subclass in Dataset.__subclasses__():
    #            #if subclass._zfs_type == kwargs['type']:
    #            #    return super(Dataset, cls).__new__(subclass, *args, **kwargs)
    #            if kwargs['type'] in ZFS_TYPE_MAP:
    #                return super(Dataset, cls).__new__(ZFS_TYPE_MAP[ kwargs['type'] ], *args, **kwargs)
    #        raise Exception, 'Dataset type not supported'
    #    elif '@' in args[0]:
    #        cls = ZFS_TYPE_MAP['snapshot']
    #    else:
    #        cls = ZFS_TYPE_MAP['filesystem']
    #    return super(Dataset, cls).__new__(cls, *args, **kwargs)


class SnapshottableDataset(object):
    pass


class Filesystem(zfs.Filesystem, SnapshottableDataset, Dataset):
    #children = mongoengine.ListField(mongoengine.ReferenceField(Dataset, reverse_delete_rules=CASCADE))
    pass


class Snapshot(zfs.Snapshot, SnapshottableDataset, Dataset):
    pass


class Snapshot(Dataset, zfs.Snapshot):
    pass


ZFS_TYPE_MAP = {
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Snapshot,
    'snapshot': Snapshot,
    }

zfs.ZFS_TYPE_MAP = ZFS_TYPE_MAP
