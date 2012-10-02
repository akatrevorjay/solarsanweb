
from django.core.cache import cache
from django.conf import settings
from storage.models import Pool, Filesystem, Volume
import storage.target as target
import random
import logging
import functools
import mongoengine.queryset

#import copy


def _timeout():
    # One minute for dev, 5 minutes for prod
    timeout = settings.DEBUG and 60 or 300
    # Tack on a random few seconds to avoid thrashing, even though I doubt that will
    # ever be an issue.
    return timeout + random.randint(1, 10)



class SingletonQuerySet(mongoengine.queryset.QuerySet):
    _objs = {}
    def __getitem__(self, key):
        if key in self._objs:
            return self._objs[key]
        else:
            return super(SingletonQuerySet, self).__getitem__(self, key)



class ListQuerySet(list):
    objects = None
    def __init__(self, document, init=True, fill=True, state=None):
        if init:
            self.objects = document.objects.clone()
        if state:
            self.__setstate__(state)
        if fill:
            self.fill()

    def fill(self):
        del self[:]
        self.extend(
            filter(lambda x: x not in self,
                  list(self.objects.all()))
        )

    def __getitem__(self, key):
        try:
            ret = list.__getitem__(self, key)
        except IndexError:
            self.fill()
            ret = list.__getitem__(self, key)
        return ret

    #def __list__(self):
    #    pass

    def __getstate__(self):
        ret = {}

        ret['self'] = self.__dict__.copy()
        objects = ret['self'].pop('objects')

        ret['data'] = list(self)

        ret['objects'] = objects.__dict__.copy()
        ret['objects'].pop('_collection_obj')

        #cursor_obj = ret['objects'].pop('_cursor_obj')
        ret['objects'].pop('_cursor_obj')
        #if cursor_obj:
        #    ret['cursor'] = cursor_obj.__dict__.copy()
        #    ret['cursor'].pop('_Cursor__collection')

        return ret

    def __setstate__(self, ret):
        self.__dict__ = ret['self']

        document = ret['objects']['_document']
        self.objects = document.objects.clone()
        self.objects.__dict__.update(ret['objects'])
        #self.objects.__dict__ = ret['objects']

        #del self[:]
        #self.extend(ret['data'])


def _model_cache(cls):
    name = '%ss' % cls.__name__.lower()
    d = cache.get(name, None)
    if d == None:
        objs = ListQuerySet(cls, fill=False, init=True, state=d)

        #objs = cls.objects.__class__(cls, cls._collection)
        #logging.debug('got objdict from cache: objdict=%s', objdict)
        #logging.debug('got objs from cache: objs=%s', objs)
    else:
        objs = ListQuerySet(cls)
        #objs = cls.objects.all()

        objdict = objs.__getstate__()
        #logging.debug('new objs=%s', objdict)

        cache.set(name, objdict, _timeout())

    return objs


def pools(request):
    ret = {}

    pools      = _model_cache(Pool)
    filesystems = _model_cache(Filesystem)
    volumes    = _model_cache(Volume)

    targets = cache.get('targets', None)
    if targets == None:
        targets = target.list()
        cache.set('targets', targets, _timeout())

    ret = {'pools': pools,
          'filesystems': filesystems,
          'volumes': volumes,
          'targets': targets,
          }
    return ret


def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}


