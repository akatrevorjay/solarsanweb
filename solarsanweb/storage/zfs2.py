
from storage.models import zPool, zDataset
#from storage.models import zPool as Pool, zDataset as Dataset
import zfs.objects as zfs

import logging, datetime, time

from mongoengine import *
import mongoengine
#from django_extensions.mongodb.models import TimeStampedModel, TitleSlugDescriptionModel, ActivatorModelManager, ActivatorModel
from django_extensions.mongodb.models import *
from django_extensions.mongodb.fields import *

zfsMongoMap = {
        'pool': {
            'mongo': zPool,
            'zfs': zfs.Pool,
            },
        'dataset': {
            'mongo': zDataset,
            'zfs': zfs.Dataset,
            },
        'filesystem': {
            'mongo': zDataset,
            'zfs': zfs.Filesystem,
            },
        'snapshot': {
            'mongo': zDataset,
            'zfs': zfs.Snapshot,
            },
        'volume': {
            'mongo': zDataset,
            'zfs': zfs.Volume,
            },
        }


#class zfsBase(zfs.zfsBase):
#    def __init__(self, *args, **kwargs):
#        map = self._mongo_map = zfsMongoMap[self._zfs_type]
#        super(zfsBaseMongo, self).__init__(*args, **kwargs)
#        dbo = self.dbo = col.find({'name': self.name})
#        if not dbo:
#            dbo = None


#class Log(Document):
#    ip_address = StringField()
#    meta = {'max_documents': 1000, 'max_size': 2000000}


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


class Filesystem(Dataset, zfs.Filesystem):
    pass


class Volume(Dataset, zfs.Volume):
    pass


