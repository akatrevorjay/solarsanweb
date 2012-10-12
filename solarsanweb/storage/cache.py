
from django.utils.datastructures import SortedDict
#from solarsan.utils import DefaultDictCache, QuerySetCache
from storage.models import Pool, Filesystem, Volume, Snapshot
import logging

"""
class FilesystemCache(QuerySetCache):
    document = Filesystem

class PoolCache(QuerySetCache):
    document = Pool

class SnapshotCache(QuerySetCache):
    document = Snapshot

class VolumeCache(QuerySetCache):
    document = Volume

Filesystem = FilesystemCache()
Pool = PoolCache()
Volume = VolumeCache()
Snapshot = SnapshotCache()
"""

from django.conf import settings
from storage.models import Pool, Filesystem, Volume, Snapshot
#import storage.cache
import random

#from solarsan.utils import DefaultDictCache, QuerySetCache
from solarsan.utils import RandTimeoutRangeCacheDict

cache = RandTimeoutRangeCacheDict()
cache.prefix = 'storage.cache'


class ListQuerySetWrapper(list):
    objects = None

    def __init__(self, document, init=True, fill=True):
        if init:
            self.objects = document.objects.clone()
        if fill:
            self._fill()

    def _fill(self, data=None, clear=True):
        if clear:
            del self[:]
        if not data:
            data = list(self.objects.all())
        self.extend(data)

    def __getitem__(self, key):
        if key not in self:
            try:
                self[key] = self.objects.get(name=key)
            except:
                pass
        return list.__getitem__(self, key)

    def __getstate__(self):
        ret = {}

        # self
        ret['self'] = self.__dict__.copy()
        # objects
        objects = ret['self'].pop('objects')
        ret['objects'] = objects.__dict__.copy()
        ret['objects'].pop('_collection_obj')
        ret['objects'].pop('_cursor_obj')
        # data
        ret['data'] = list(self)

        return ret

    def __setstate__(self, ret):
        # self
        self.__dict__.update(ret['self'])
        # objects
        document = ret['objects']['_document']
        self.__init__(document, init=True, fill=False)
        ret['objects']['_cursor_obj'] = self.objects._cursor_obj
        ret['objects']['_collection_obj'] = self.objects._collection_obj
        self.objects.__dict__.update(ret['objects'])
        # data
        self._fill(data=ret['data'])


def _get_model_cache(cls, force=None):
    name = cls.__name__.lower() + 's'
    ret = None
    if not force:
        ret = cache.get(name)
    if ret is None:
        ret = ListQuerySetWrapper(cls)
        cache.set(name, ret)
    return ret


def pools(*arg):
    return _get_model_cache(Pool, *arg)


def filesystems(*arg):
    return _get_model_cache(Filesystem, *arg)


def volumes(*arg):
    return _get_model_cache(Volume, *arg)


import storage.target


def targets(force=None):
    name = 'targets'
    ret = None
    if not force:
        ret = cache.get(name)
    if ret is None:
        ret = storage.target.target_list()
        cache.set(name, ret)
    return ret


def storage_objects(null=None):
    return SortedDict([
        ('pools', pools()),
        ('filesystems', filesystems()),
        ('volumes', volumes()),
        ('targets', targets()),
    ])
