
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

"""
Mongo
"""

class PropertyDocument(m.EmbeddedDocument):
    name = m.StringField(required=True, unique=True)
    value = m.StringField()

    #created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    #modified = m.DateTimeField(default=datetime.now())

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


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
    enabled = m.BooleanField()

    #def __init__(self, *args, **kwargs):
    #    # Apparently m.Document accepts no init *args
    #    super(zfsBaseDocument, self).__init__(**kwargs)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)


class VDevBase(m.EmbeddedDocument):
    meta = {'abstract': True,
            'ordering': ['-created']}

    VDEV_TYPES=['root', 'mirror', 'disk']
    type = m.StringField(required=True, choices=VDEV_TYPES)
    id = m.IntField()
    guid = m.StringField(unique=True, required=True, primary_key=True)

    created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)


class VDevRoot(VDevBase):
    pool_guid = m.StringField()
    state = m.IntField()
    txg = m.IntField()
    pass


class VDevDisk(VDevBase):
    ashift = m.IntField()
    asize = m.IntField()
    create_txg = m.IntField()
    # Only on mirrored vdevs
    DTL = m.IntField()
    resilvering = m.IntField()
    is_log = m.IntField()
    metaslab_array = m.IntField()
    metaslab_shift = m.IntField()
    path = m.StringField()
    whole_disk = m.IntField()
    pass




class VDevPool(VDevBase):
    version = m.IntField()
    name = m.StringField()
    state = m.IntField()
    txg = m.IntField()
    hostname = m.StringField()

    vdev_children = m.IntField()
    vdev_tree = m.MapField(m.EmbeddedDocumentField(VDevRoot))

    #def children(self):
    #    pass



class PoolDocument(zfsBaseDocument):
    meta = {'collection': 'pools'}
    version = m.IntField()
    state = m.IntField()
    txg = m.IntField()
    pool_guid = m.StringField(unique=True, required=True, primary_key=True)
    hostname = m.StringField()
    #vdev_children = m.IntField()
    vdev_tree = m.MapField(field=m.EmbeddedDocumentField(VDevRoot))
    pass



class DatasetDocument(zfsBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True}
    pool = m.ReferenceField(PoolDocument,
                            reverse_delete_rule=m.CASCADE)
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
