
import zfs.objects as zfs
import logging, datetime, time

from mongoengine import *
import mongoengine
#from django_extensions.mongodb.models import TimeStampedModel, TitleSlugDescriptionModel, ActivatorModelManager, ActivatorModel
#from django_extensions.mongodb.models import *
#from django_extensions.mongodb.fields import *


class TimestampedDocument(mongoengine.Document):
    meta = {'collection': 'storage_base',
            'allow_inheritance': True,
            }
    #abstract = True
    created = DateTimeField(default=datetime.datetime.now())
    modified = DateTimeField(default=datetime.datetime.now())


#class Property(mongoengine.EmbeddedDocument, zfs.Property):
class Property(mongoengine.EmbeddedDocument):
    name = StringField(required=True)
    value = StringField(required=True)
    source = StringField()

    def __str__(self):
        return str(self.value)
    def __unicode__(self):
        return unicode(self.value)
    def __repr__(self):
        return "Property(name=%s, value=%s, source=%s)" % (self.name, self.value, self.source)
    def __call__(self, *args, **kwargs):
        """ Sets property with value """
        #if hasattr(self, 'parent'): self.parent.set(self.name, value)
        return super(Property, self).__call__(*args, **kwargs)



class zfsBaseMongo(TimestampedDocument):
    meta = {'collection': 'storage_base',
            'allow_inheritance': True,
            'indexes': [{'fields': ['name'], 'unique': True}],
            }
    #abstract = True
    name = StringField(required=True, unique=True)
    props = ListField(EmbeddedDocumentField(Property))



class Pool(zfsBaseMongo, zfs.Pool):
    meta = {'collection': 'storage_pools',
            }

    ## TODO Should this be overriden to return db data or should the mongo object's attrs return db data,
    ##   but whenever list() or get() are called, it automatically updates those objects?
    #def list(self, *args, **kwargs):
    #    super(Pool, self).list(*args, **kwargs)
    #def get(self, *args, **kwargs):
    #    super(Pool, self).list(*args, **kwargs)


class Dataset(zfsBaseMongo, zfs.Dataset):
    #pool = ReferenceField(Pool, reverse_delete_rule=CASCADE)
    meta = {'collection': 'storage_datasets',
            }

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


#class SnapshottableDataset(zfs.SnapshottableDataset):
class SnapshottableDataset(object):
    pass


class Filesystem(Dataset, SnapshottableDataset, zfs.Filesystem):
    pass


class Volume(Dataset, SnapshottableDataset, zfs.Volume):
    pass


class Snapshot(Dataset, zfs.Snapshot):
    pass



ZFS_TYPE_MAP = {
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    }

zfs.ZFS_TYPE_MAP = ZFS_TYPE_MAP


