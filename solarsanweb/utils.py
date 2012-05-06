
class FilterableDict(dict):
    """ Filter dict contents by str(key), list(keys), dict(key=value) """

    def filter(self, *args, **kwargs):
        """ Filter dict object contents by str(key), list(keys), dict(key=value) where contents are an object and dict(key=value) are matched on obj.data """
        items = self.iteritems()
        for filter in list( list(*args) + [dict(**kwargs)] ):
            if not len(filter) > 0:
                continue
            filter_type = str(type(filter))
            if filter_type=="<type 'str'>":
                items = [(k,v) for (k,v) in items if k == filter]
            elif filter_type=="<type 'list'>":
                items = [(k,v) for (k,v) in items if k in filter]
            elif filter_type=="<type 'dict'>":
                items = [ (k,v) for (k,v) in items
                            for (kwk, kwv) in kwargs.items()
                              if v.get(kwk) == kwv ]
        new = self.__new__(self.__class__, *list(items))
        return new

class CachedFunc(object):
    __name__ = "<unknown>"
    """ Cached function or property """
    def __init__(self, func=None, ttl=300):
        self.ttl = ttl
        self.__set_func(func)
    def __set_func(self, func=None, doc=None):
        if not func:
            return False
        self.func = func
        self.__doc__ = doc or self.func.__doc__
        self.__name__ = self.func.__name__
        self.__module__ = self.func.__module__
    def __call__(self, func=None, doc=None, *args, **kwargs):
        if func:
            self.__set_func(func, doc)
            return self
        now = time.time()
        try:
            value, last_update = self._cache
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.func(*args, **kwargs)
            self._cache = (value, now)
        return value
    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.func(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value
    def __repr__(self):
        return "<@CachedFunc: '%s'>" % self.__name__

import random
@CachedFunc(ttl=3)
def cachefunc_tester(*args, **kwargs):
    return random.randint(0,100)

