
from solarsan.utils import DefaultDictCache, QuerySetCache
from storage.models import Pool, Filesystem, Volume, Snapshot


class FilesystemCache(QuerySetCache):
    document = Filesystem
Filesystem = FilesystemCache()

class PoolCache(QuerySetCache):
    document = Pool
Pool = PoolCache()

class SnapshotCache(QuerySetCache):
    document = Snapshot
Snapshot = SnapshotCache()

class VolumeCache(QuerySetCache):
    document = Volume
Volume = VolumeCache()


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
        try:
            ret = list.__getitem__(self, key)
        except IndexError:
            self._fill()
            ret = list.__getitem__(self, key)
        return ret

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
        #self.__dict__ = ret['self']
        self.__dict__.update(ret['self'])

        # objects
        document = ret['objects']['_document']
        self.__init__(document, init=True, fill=False)
        ret['objects']['_cursor_obj'] = self.objects._cursor_obj
        ret['objects']['_collection_obj'] = self.objects._collection_obj

        #self.objects.__dict__ = ret['objects']
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

    objs = cache.get(name, None)
    if objs is None:
        objs = ListQuerySet(cls)
        cache.set(name, objs, _timeout())

    return objs


import storage.target


class StorageObjects(object):
    last_ret = None
    last_req_id = None

    def __name__(self):
        return 'storage_objects'

    def __call__(self, request):
        if self.last_req_id == request:
            return self.last_ret
        ret = {}

        pools = _model_cache(Pool)
        filesystems = _model_cache(Filesystem)
        volumes = _model_cache(Volume)

        targets = cache.get('targets', None)
        if targets is None:
            targets = storage.target.list(cached=False)
            cache.set('targets', targets, _timeout())

        ret = {'pools': pools,
               'filesystems': filesystems,
               'volumes': volumes,
               'targets': targets, }
        self.last_req_id = request
        self.last_ret = ret
        return ret


storage_objects = StorageObjects()