
from django.core.cache import cache
from django.conf import settings
from storage.models import Pool, Filesystem, Volume
import storage.target as target
import random
import logging
import functools
import mongoengine.queryset

#import copy


def pickle_getstate(self):
    col = None
    objdict = self.__dict__.copy()

    curdict = None
    cursor = objdict.get('_cursor_obj', col)
    if cursor:
        cursor = cursor.clone()
        objdict['_cursor_obj'] = cursor
        cursor.__dict__.pop('_Cursor__collection')

    objdict['_collection_obj'] = col

    return objdict


def pickle_setstate(self, objdict):
    col = objdict['_document']._collection
    objdict.update({'_collection_obj': col, })

    cursor = objdict.get('_cursor_obj')
    if cursor:
        cursor.__dict__.update({'_Cursor__collection': col, })

    self.__dict__.update(objdict)


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
    def __init__(self, document, init=True, fill=True):
        if init:
            self.objects = document.objects.clone()
        if fill:
            self.fill()

    def fill(self):
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
            #ret = self[key] = super(ListQuerySet, self).__getitem__(key)
        return ret

    #def __list__(self):
    #    pass




def _model_cache(cls):
    name = '%ss' % cls.__name__.lower()
    objdict = cache.get(name)
    if objdict:
        objs = ListQuerySet(cls, fill=False)
        #objs = cls.objects.__class__(cls, cls._collection)
        pickle_setstate(objs.objects, objdict)

        #logging.debug('got objdict from cache: objdict=%s', objdict)
        #logging.debug('got objs from cache: objs=%s', objs)
    else:
        objs = ListQuerySet(cls)
        #objs = cls.objects.all()

        objdict = pickle_getstate(objs.objects)
        #logging.debug('new objs=%s', objdict)

        cache.set(name, objdict, _timeout())

    return objs


def pools(request):
    ret = {}

    pools      = _model_cache(Pool)
    filesystems = _model_cache(Filesystem)
    volumes    = _model_cache(Volume)

    targets = cache.get('targets')
    if not targets:
        targets = target.list(cached=True)
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


