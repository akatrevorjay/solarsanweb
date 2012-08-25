
import mongoengine as m
from datetime import datetime


"""
Mongo
"""


class PropertyDocument(m.EmbeddedDocument):
    name = m.StringField(required=True, unique=True)
    value = m.StringField()

    #created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    #modified = m.DateTimeField(default=datetime.now())

    pass


class zfsBaseDocument(m.Document):
    meta = {'abstract': True,
            'ordering': ['-created']}
    name = m.StringField(required=True, unique=True)
    #type = m.StringField(required=True)
    #name = m.StringField()
    # TODO Need to make this store as a dict in parent too
    props = m.MapField(m.EmbeddedDocumentField(PropertyDocument))
    #misc = m.DictField()
    importing = m.BooleanField()

    created = m.DateTimeField(default=datetime.now())
    # TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())

    #def __init__(self, *args, **kwargs):
    #    # Apparently m.Document accepts no init *args
    #    super(zfsBaseDocument, self).__init__(**kwargs)



class PoolDocument(zfsBaseDocument):
    meta = {'collection': 'pools'}
    pass


class DatasetDocument(zfsBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True}
    pool = m.ReferenceField(PoolDocument,
                            reverse_delete_rule=m.DENY)
    parent = m.GenericReferenceField()
    pass


class FilesystemDocument(DatasetDocument):
    pass

class VolumeDocument(DatasetDocument):
    pass

class SnapshotDocument(DatasetDocument):
    pass

ZFS_MONGO_MAP = {
        'pool':         PoolDocument,
        'dataset':      DatasetDocument,
        'filesystem':   FilesystemDocument,
        'volume':       VolumeDocument,
        'snapshot':     SnapshotDocument,
    }
