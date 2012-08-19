
import zfs.objects as zfs
import mongoengine
#from mongoengine import *

import logging
import datetime
import time



class Wrapper(object):
    _wrapped_cls = None
    _wrapped_obj = None
    _wrapped_obj_always = []
    def __init__(self, *args, **kwargs):
        if not getattr(self, '_wrapped_cls'):
            raise Exception('No class was given to wrap')
        self._wrapped_obj = self._wrapped_cls(*args, **kwargs)
        super(Wrapper, self).__init__()
    def __getattr__(self, attr):
        # See if this object has attr; don't use hasattr unless you like loops.
        if attr in self.__dict__ and not attr in getattr(self, '_wrapped_obj_always'):
            return getattr(self, attr)
        # Proxy
        return getattr(self._wrapped_obj, attr)
    def _wrapped_proxy(self, attr):
        return getattr(self._wrapped_obj, attr)





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
    meta = {'abstract': True}

    _wrapped_zfs = None
    _wrapped_db = None
    _wrapped_zfs_cls = None
    _wrapped_db_cls = zfsBaseDocument
    #_wrapped_zfs_always = []
    #_wrapped_db_always = []

    def __init__(self, *args, **kwargs):
        if not getattr(self, '_wrapped_zfs_cls'):
            raise Exception('No class was given to wrap')

        if not 'name' in kwargs and args:
            if not isinstance(args, list):
                args = isinstance(args, basestring) and [args] or list(args)
            name = args.pop(0)
            kwargs['name'] = name

        self._wrapped_zfs = self._wrapped_zfs_cls(name)
        self._wrapped_db = self._wrapped_db_cls(**kwargs)

        super(zfsBase, self).__init__()

    def __repr__(self):
        return 'Solar%s' % self._wrapped_obj.__repr__()

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)

        for obj in [self._wrapped_zfs, self._wrapped_db]:
            if attr in obj.__dict__:
                return getattr(obj, attr)




class Pool(zfsBase):
    meta = {'collection': 'storage_pools'}
    _wrapped_zfs_cls = zfs.Pool


class Dataset(zfsBase):
    meta = {'collection': 'storage_datasets'}
    _wrapped_zfs_cls = zfs.Dataset


class Filesystem(zfsBase):
    meta = {'collection': 'storage_datasets'}
    _wrapped_zfs_cls = zfs.Filesystem


class Volume(zfsBase):
    meta = {'collection': 'storage_datasets'}
    _wrapped_zfs_cls = zfs.Volume


class Snapshot(zfsBase):
    meta = {'collection': 'storage_datasets'}
    _wrapped_zfs_cls = zfs.Snapshot


#ZFS_TYPE_MAP = {
#    'pool': Pool,
#    'dataset': Dataset,
#    'filesystem': Filesystem,
#    'volume': Volume,
#    'snapshot': Snapshot,
#    }

#zfs.ZFS_TYPE_MAP = ZFS_TYPE_MAP




##class Property(mongoengine.EmbeddedDocument, zfs.Property):
#class Property(mongoengine.EmbeddedDocument):
#    meta = {'abstract': True,
#            }
#    name = mongoengine.StringField(required=True)
#    value = mongoengine.StringField(required=True)
#    source = mongoengine.StringField()
#    created = mongoengine.DateTimeField(default=datetime.datetime.now())
#    modified = mongoengine.DateTimeField(default=datetime.datetime.now())
3
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





#class zfsBase(zfs.zfsBase):
    #pass

    #meta = {
    #        #'allow_inheritance': False,
    #        #'indexes': [{'fields': ['name'], 'unique': True, 'sparse': True, 'types': False}],
    #        #'indexes': [{'fields': ['name'], 'unique': True, 'sparse': True,}],
    #        #'indexes': [{'fields': ['name'], 'unique': True}],
    #        }
    #name = mongoengine.StringField(required=True, unique=True)
    #name = mongoengine.StringField()
    #enabled = mongoengine.BooleanField(default=True)
    # TODO Need to make this store as a dict in parent too
    #props = mongoengine.DictField()

    #created = mongoengine.DateTimeField(default=datetime.datetime.now())
    #modified = mongoengine.DateTimeField(default=datetime.datetime.now())


    ##
    ## TODO Figure out how to handle the procedure of ensuring proper order
    ##   of events has happened, ie do not save in db if it's not yet created,
    ##   etc
    ##

    #def get(self, *args, **kwargs):
    #    # With a Mongo backend, the props for self are stored in the document for the parent object.
    #    pass
    #
    #    # We may want to resort to going direct in certain cases however, so keeping this here until we may.
    #    #return super(self).get(*args, **kwargs)

    #def zfs(self):
    #    """ Backwards compat, but I doubt this will be needed """
    #    return self





#class Pool(zfs.Pool, mongoengine.Document):
#    meta = {'collection': 'storage_pools',
#            #'abstract': True,
#            #'allow_inheritance': False,
#            }
#    #filesystem = mongoengine.ReferenceField(Filesystem, reverse_delete_rule=CASCADE)

#    #meta = {}
#    name = mongoengine.StringField(required=True, unique=True)
#    #name = mongoengine.StringField()
#    enabled = mongoengine.BooleanField(default=True)
#    # TODO Need to make this store as a dict in parent too
#    #props = mongoengine.DictField()

#    created = mongoengine.DateTimeField(default=datetime.datetime.now())
#    modified = mongoengine.DateTimeField(default=datetime.datetime.now())

#    ##
#    ## TODO Should this be overriden to return db data or should the mongo object's attrs return db data,
#    ##   but whenever list() or get() are called, it automatically updates those objects?
#    ##

#    #def list(self, *args, **kwargs):
#    #    super(Pool, self).list(*args, **kwargs)

#    #def get(self, *args, **kwargs):
#    #    super(Pool, self).list(*args, **kwargs)


#class Dataset(zfs.Dataset, mongoengine.Document):
#    #pool = mongoengine.ReferenceField(Pool, reverse_delete_rule=CASCADE)

#    meta = {'collection': 'storage_datasets'}
#    name = mongoengine.StringField(required=True, unique=True)
#    #name = mongoengine.StringField()
#    enabled = mongoengine.BooleanField(default=True)
#    # TODO Need to make this store as a dict in parent too
#    #props = mongoengine.DictField()

#    created = mongoengine.DateTimeField(default=datetime.datetime.now())
#    modified = mongoengine.DateTimeField(default=datetime.datetime.now())

#    #def __init__(self, name, *args, **kwargs):
#    #    super(Dataset, self).__init__(name, *args, **kwargs)

#    #def __new__(cls, *args, **kwargs):
#    #    if 'type' in kwargs:
#    #        for subclass in Dataset.__subclasses__():
#    #            #if subclass._zfs_type == kwargs['type']:
#    #            #    return super(Dataset, cls).__new__(subclass, *args, **kwargs)
#    #            if kwargs['type'] in ZFS_TYPE_MAP:
#    #                return super(Dataset, cls).__new__(ZFS_TYPE_MAP[ kwargs['type'] ], *args, **kwargs)
#    #        raise Exception, 'Dataset type not supported'
#    #    elif '@' in args[0]:
#    #        cls = ZFS_TYPE_MAP['snapshot']
#    #    else:
#    #        cls = ZFS_TYPE_MAP['filesystem']
#    #    return super(Dataset, cls).__new__(cls, *args, **kwargs)
#    pass


#class Filesystem(zfs.Filesystem, mongoengine.Document):
#    meta = {'collection': 'storage_datasets',
#            }

#    #children = mongoengine.ListField(mongoengine.ReferenceField(Dataset, reverse_delete_rules=CASCADE))
#    pass


#class Snapshot(zfs.Snapshot, mongoengine.Document):
#    pass




