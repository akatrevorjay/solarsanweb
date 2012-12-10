"""
What file? Oh THIS file you say?
For the record, I have no idea what you're talking about. ;)
  ~trevorj
"""


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

    #if getattr(mongoengine.queryset.QuerySet, 'use_cache', True) is not None:
    #    _old_QuerySet = mongoengine.queryset.QuerySet
    #    mongoengine.queryset.QuerySet = QuerySet

#patch_queryset()

import rtslib
import storage.models


def patch_rtslib():
    """ Monkeypatch RTSLib """
    # Common
    def dumps(self):
        return self.__dict__

    def __repr__(self):
        name = getattr(self, 'wwn', None)
        if not name:
            return super(self.__class__, self).__repr__()
        return '<%s %s>' % (self.__class__.__name__, name)

    # StorageObject
    cls = rtslib.tcm.StorageObject
    if not getattr(cls, 'dumps', None):
        def get_volume(self):
            """ Get Storage Volume for this object """
            return storage.models.Volume.objects.get(backstore_wwn=self.wwn)
        setattr(cls, 'get_volume', get_volume)
        setattr(cls, 'dumps', dumps)
        setattr(cls, '__repr__', __repr__)

    # Target
    cls = rtslib.target.Target
    if not getattr(cls, 'dumps', None):
        def short_wwn(arg):
            """ Shorten WWN string """
            if not isinstance(arg, basestring):
                arg = arg.wwn
            return arg.split(':', 2)[1]
        setattr(cls, 'short_wwn', short_wwn)

        def get_tpg(self, tag=0):
            for x in self.tpgs:
                if x.tag == tag:
                    return x
                    break
            raise Exception("Could not find TPG with tag='%s' for Target with '%s'", tag, self)
        setattr(cls, 'get_tpg', get_tpg)
        setattr(cls, 'dumps', dumps)
        setattr(cls, 'type', 'target')
        setattr(cls, '__repr__', __repr__)
        #def get_absolute_url(self):
        #    return reverse(self.__class__.__name__.lower(), kwargs={'slug': self.wwn})
        #setattr(cls, 'get_absolute_url', get_absolute_url)

    # TPG
    cls = rtslib.target.TPG
    if not getattr(cls, 'dumps', None):
        setattr(cls, 'dumps', dumps)

        def __repr__(self):
            target = getattr(self, 'parent_target', None)
            if not target:
                return super(self.__class__, self).__repr__()
            tag = getattr(self, 'tag', None)
            enable = getattr(self, 'enable', None)
            return '<%s tag=%s, enabled=%s parent_target_wwn=%s>' % (self.__class__.__name__, tag, enable, target.wwn)
        setattr(cls, '__repr__', __repr__)

    # NodeACL
    cls = rtslib.target.NodeACL
    if not getattr(cls, 'dumps', None):
        setattr(cls, 'dumps', dumps)

        def __repr__(self):
            tpg = getattr(self, 'parent_tpg', None)
            target = getattr(tpg, 'parent_target', None)
            if not target or not tpg:
                return super(self.__class__, self).__repr__()
            tag = getattr(tpg, 'tag', 'None')
            node_wwn = getattr(self, 'node_wwn', 'None')
            auth_target = getattr(self, 'authenticate_target', 'null')
            luns = list(getattr(self, 'mapped_luns', 'null'))
            sessions = getattr(self, 'session', 'null')
            if not  sessions: sessions = ['carp']
            if not  luns: luns = ['carp']


            return '<%s node_wwn=%s, auth_target=%s, luns=%s, sessions=%s tpg_tag=%s, target_wwn=%s>' % \
                (self.__class__.__name__, node_wwn, auth_target, len(luns), len(sessions), tag, target.wwn)
        setattr(cls, '__repr__', __repr__)

patch_rtslib()

