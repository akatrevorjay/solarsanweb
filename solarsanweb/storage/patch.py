
import mongoengine.queryset

def patch_queryset():
    class QuerySet(mongoengine.queryset.QuerySet):
        """ QuerySet wrapper that caches results
        """
        use_cache = None

        def __init__(self, *args, **kwargs):
            use_cache = kwargs.pop('use_cache', None)
            if use_cache is not None:
                self.use_cache = use_cache
            return super(QuerySet, self).__init__(*args, **kwargs)

        def rewind(self):
            self._cache = None
            return super(QuerySet, self).rewind()

        #def next(self):
        #    ret = super(QuerySet, self).next()
        #    if self.use_cache and self._cache is not None:
        #        self._cache.append(ret)
        #    return ret

        #def count(self):
        #    if self.use_cache and self._cache is not None:
        #        return len(self._cache)

        def __iter__(self):
            if self.use_cache:
                hashes = {'dict': hash(self.__dict__),
                          'query': hash(self._query), }
                mhash = hash(hashes)
                if self._cache and self._cache_mhash == mhash:
                    return iter(self._cache)
                else:
                    self._cache = []
                    self._cache_mhash = mhash
            return super(QuerySet, self).__iter__()

        def __getstate__(self):
            ret = self.__dict__.copy()
            ret.pop('_collection_obj')
            ret.pop('_cursor_obj')
            return ret

        def __setstate__(self, ret):
            document = ret['_document']
            self.__init__(document, document._collection)
            #ret['_cursor_obj'] = self._cursor_obj
            #ret['_collection_obj'] = self._collection_obj
            self.__dict__.update(ret)

    if getattr(mongoengine.queryset.QuerySet, 'use_cache', True) is not None:
        _old_QuerySet = mongoengine.queryset.QuerySet
        mongoengine.queryset.QuerySet = QuerySet

patch_queryset()

import rtslib
import storage.models

def patch_rtslib():
    """ Monkeypatch RTSLib """
    # StorageObject
    cls = rtslib.tcm.StorageObject
    if not getattr(cls, 'get_volume', None):
        def get_volume(self):
            """ Get Storage Volume for this object """
            return storage.models.Volume.objects.get(backstore_wwn=self.wwn)
        setattr(cls, 'get_volume', get_volume)

    # Target
    cls = rtslib.target.Target
    if not getattr(cls, 'short_wwn', None):
        def short_wwn(arg):
            """ Shorten WWN string """
            if not isinstance(arg, basestring):
                arg = arg.wwn
            return arg.split(':', 2)[1]
        setattr(cls, 'short_wwn', short_wwn)

        setattr(cls, 'type', 'target')

patch_rtslib()

