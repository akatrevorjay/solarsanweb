
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

from django.core.cache import cache
from django.conf import settings
from storage.models import Pool, Filesystem, Volume, Snapshot
#import storage.cache
import random

from solarsan.utils import DefaultDictCache, QuerySetCache


class ListQuerySet(list):
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


def _timeout():
    # One minute for dev, 5 minutes for prod
    timeout = settings.DEBUG and 60 or 300
    # Tack on a random few seconds to avoid thrashing, even though I doubt that will
    # ever be an issue.
    return timeout + random.randint(1, 10)


def _model_cache(cls):
    name = '%ss' % cls.__name__.lower()
    ret = cache.get(name, None)
    if ret is None:
        ret = ListQuerySet(cls)
        cache.set(name, ret, _timeout())
    return ret


def pools(*arg):
    return _model_cache(Pool, *arg)


def filesystems(*arg):
    return _model_cache(Filesystem, *arg)


def volumes(*arg):
    return _model_cache(Volume, *arg)


import storage.target


def targets(*args):
    name = 'targets'
    ret = cache.get(name, None)
    if ret is None:
        ret = storage.target.target_list()
        cache.set(name, ret, _timeout())
    return ret


def storage_objects(request):
    return {'pools': pools(),
             'filesystems': filesystems(),
             'volumes': volumes(),
             'targets': targets(), }