
#from django.db import models
#from jsonfield import JSONField
#import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
#import zfs
#import zfs.objects
#import zfs.cmd

#import mongoengine as m
#from datetime import datetime
#from django.utils import timezone

#from django.core.urlresolvers import reverse

# Start blank, add in defaults. At the bottom of this file customizations are done.
ZFS_TYPE_MAP = {}
#ZFS_TYPE_MAP.update(zfs.objects.ZFS_TYPE_MAP)

#from .base import zfsBaseDocument, zfsBase


from dj import reverse

from datetime import datetime
import mongoengine as m

import zfs
import zfs.objects

#from . import ZFS_TYPE_MAP



"""
Base
"""


class ReprMixIn(object):
    def __repr__(self):
        for k in ['name', 'guid', 'id']:
            name = getattr(self, k, None)
            if name:
                break
        return "<%s: %s>" % (self.__class__.__name__, name)

    def __unicode__(self):
        name = getattr(self, 'name', self.__repr__())
        return name


class BaseMixIn(ReprMixIn):
    @property
    def short_type(self):
        if type == 'filesystem':
            return 'FS'
        elif type == 'pool':
            return 'POOL'
        elif type == 'volume':
            return 'VOL'
        else:
            return 'TGT'


#class BaseDocument(BaseMixIn, m.Document):
#    meta = {'abstract': True,}


"""
Base Document
"""


from .props import Property


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

    def get_absolute_url(self, *args):
        """ Gets URL for object """
        name = getattr(self, 'name', None)
        type = getattr(self, 'type', None)
        assert name
        assert type
        return reverse(type, None, None, {'slug': name, }, )

    def dumps(self):
        return self.__dict__


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


import zfs.objects
from .pool import PoolDocument


class Pool(PoolDocument, zfs.objects.PoolBase, zfsBase):
    @property
    def filesystem(self):
        """ Returns the matching Filesystem for this Pool """
        assert self.name, "Cannot get filesystem for unnamed Pool"
        obj, created = Filesystem.objects.get_or_create(name=self.name, pool=self, auto_save=False)
        if created:
            obj.guid = obj.get('guid')['value']
            obj.save()
        return obj

    def filesystems(self):
        return Filesystem.objects.filter(pool=self)

    def volumes(self):
        return Volume.objects.filter(pool=self)


from .filesystem import Filesystem
from .volume import Volume
from .snapshot import Snapshot
from .dataset import Dataset


# ZFS Object Map
ZFS_TYPE_MAP.update({
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    #'properties': zfs.objects.Properties,
    'property': Property,
})

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
