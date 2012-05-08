# -*- coding: utf-8 -*-

from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.db.models.base import ModelBase
import string, os, sys, logging, datetime

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


def convert_bytes_to_human(n):
    """ Utility to convert bytes to human readable (K/M/G/etc) """
    SYMBOLS = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    PREFIX = {}
    for i, j in enumerate(SYMBOLS):
        PREFIX[j] = 1 << (i+1)*10

    for i in reversed(SYMBOLS):
        if n >= PREFIX[i]:
            value = float(n) / PREFIX[i]
            return '%.1f%s' % (value, i)

def convert_human_to_bytes(s):
    """ Utility to convert human readable (K/M/G/etc) to bytes """
    SYMBOLS = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    PREFIX = {}
    for i, j in enumerate(SYMBOLS):
        PREFIX[j] = 1 << (i+1)*10

    s = str(s).upper()
    for i in SYMBOLS:
        if s.endswith(i):
            return '%.0f' % (float(s[:-1]) * PREFIX[i])

    # Must be bytes or invalid data
    #TODO What if it's invalid data? How should that be handled?
    return '%.0f' % float(s)

KEYNOTFOUND = '<KEYNOTFOUND>'       # KeyNotFound for dictDiff

def dict_diff(first, second):
    """ Return a dict of keys that differ with another config object.  If a value is
        not found in one fo the configs, it will be represented by KEYNOTFOUND.
        @param first:   Fist dictionary to diff.
        @param second:  Second dicationary to diff.
        @return diff:   Dict of Key => (first.val, second.val)
    """
    diff = {}
    # Check all keys in first dict
    for key in first.keys():
        if (not second.has_key(key)):
            diff[key] = (first[key], KEYNOTFOUND)
        elif (first[key] != second[key]):
            diff[key] = (first[key], second[key])
    # Check all keys in second dict to find missing
    for key in second.keys():
        if (not first.has_key(key)):
            diff[key] = (KEYNOTFOUND, second[key])
    return diff

#class LazyJSONEncoder(simplejson.JSONEncoder):
    #""" a JSONEncoder subclass that handle querysets and models objects. Add
    #your code about how to handle your type of object here to use when dumping
    #json """
    #def default(self,o):
        ## this handles querysets and other iterable types
        #try:
            #iterable = iter(o)
        #except TypeError:
            #pass
        #else:
            #return list(iterable)

        ## this handlers Models
        #try:
            #isinstance(o.__class__,ModelBase)
        #except Exception:
            #pass
        #else:
            #return force_unicode(o)

        #return super(LazyJSONEncoder,self).default(obj)

def serialize_to_json(obj,*args,**kwargs):
    """ A wrapper for simplejson.dumps with defaults as:

    ensure_ascii=False
    cls=LazyJSONEncoder

    All arguments can be added via kwargs """
    kwargs['ensure_ascii'] = kwargs.get('ensure_ascii',False)
    kwargs['cls'] = kwargs.get('cls',LazyJSONEncoder)

    return simplejson.dumps(obj,*args,**kwargs)

def qdct_as_kwargs(qdct):
    kwargs={}
    for k,v in qdct.items():
        kwargs[str(k)]=v
    return kwargs

