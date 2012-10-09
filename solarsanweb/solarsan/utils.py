# -*- coding: utf-8 -*-

#from django.utils import simplejson
#from django.utils.encoding import force_unicode
#from django.db.models.base import ModelBase
#import string, os, sys
import logging
import time
from django import http
import inspect
from decorator import decorator

##
## django-braces -- Nice reusable MixIns
## http://django-braces.readthedocs.org/en/latest/index.html
##
#from braces.views import LoginRequiredMixin, PermissionRequiredMixin, SuperuserRequiredMixin #, UserFormKwargsMixin, UserKwargModelFormMixIn
#from braces.views import SuccessURLRedirectListMixin, SetHeadlineMixin, CreateAndRedirectToEditView, SelectRelatedMixin

"""
DefaultDictCache/QuerySetCache
"""

from collections import defaultdict

class DefaultDictCache(defaultdict):
    def __missing__(self, key):
        value = self.get_missing_key(key)
        self[key] = value
        return value

class QuerySetCache(DefaultDictCache):
    def __init__(self, *args, **kwargs):
        for k in ['objects', 'document', 'query_kwarg']:
            if k in kwargs:
                v = kwargs.pop(k)
                setattr(self, k, v)
        if getattr(self, 'document', None):
            self.objects = self.document.objects
        self.query_kwarg = kwargs.pop('query_kwarg', 'name')
        return super(QuerySetCache, self).__init__(*args, **kwargs)

    def get_kwargs(self, key, **kwargs):
        return {self.query_kwarg: key, }

    def get_missing_key(self, key):
        kwargs = self.get_kwargs(key)
        return self.objects.get_or_create(**kwargs)[0]


"""
Singleton
"""


class Borg:
    __shared_state = {}

    def __init__(self, *args, **kwargs):
        self.__dict__ = self.__shared_state
        super(Borg, self).__init__(self, *args, **kwargs)


class Singleton:
    __single = None

    def __init__(self):
        if Singleton.__single:
            raise Singleton.__single
        Singleton.__single = self

    @classmethod
    def getinstance(cls, x=None):
        if x is None:
            x = cls
        try:
            single = x()
        except Singleton, s:
            single = s
        return single


class SingletonDecorator:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


class SingletonMeta(type):
    """
    Example:
        class MyClass(object):
            __metaclass__ = SingletonMeta
    """
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


def singleton_pep318(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

"""
class NothingSpecial:
    pass

_the_one_and_only = None

def TheOneAndOnly():
    global _the_one_and_only
    if not _the_one_and_only:
        _the_one_and_only = NothingSpecial()
    return _the_one_and_only
"""


"""
def getSystemContext(contextObjList=[]):
    if len( contextObjList ) == 0:
        contextObjList.append( Context() )
        pass
    return contextObjList[0]

class Context(object):
    # Anything you want here
"""


"""
Proxy
"""


class Proxy:
    __subject = None

    def __init__(self, subject):
        self.__subject = subject

    def __getattr__(self, name):
        return getattr(self.__subject, name)


"""
Exceptions
"""


class FormattedException(Exception):
    """Extends a normal Exception to support multiple *args used to format your message ala string formatting
    """
    def __init__(self, msg, *args, **kwargs):
        if msg and args:
            logging.exception(msg, *args)
            msg = msg % args

        # Call the base class constructor with the parameters it needs
        super(FormattedException, self).__init__(msg, **kwargs)


class LoggedException(FormattedException):
    """Logs an error when an exception occurs.
    Since it's baseclass is FormattedException it also supports formatting.
    """
    def __init__(self, *args, **kwargs):
        if args:
            logging.error(*args)
        super(LoggedException, self).__init__(*args, **kwargs)


"""
Decorators
"""

@decorator
def trace(f, *args, **kw):
    print "calling %s with args %s, %s" % (f.func_name, args, kw)
    return f(*args, **kw)

@decorator
def args_list(f, *args, **kwargs):
    if not isinstance(args, list):
        args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
    return f(*args, **kwargs)

"""
Cache Helpers
"""

from django.core import cache
class CacheDict(dict):
    prefix = 'zfs_obj_tree'
    ttl = 15
    def __getitem__(self, key):
        print 'get key=%s' % key
        return cache.get('%s__%s' % (self.prefix, key))
    def __setitem__(self, key, value):
        print 'set key=%s value=%s' % (key, value)
        cache.set('%s__%s' % (self.prefix, key), value, self.ttl)


"""
Devel helpers
"""

class TrueDebug(object):
    ### Alpha ###
    """A simple debugger. Add debug() to a function and it prints the function name and any objects included.
    Adding True to locale prints the file name where the function is. Adding False to log turns the log off.
    This feature can be modified to trace deeper and find the bugs faster, ending the puzzle box."""
    def __init__(self, objects=None, locale=False, log=True, parents=False):
        if log == False: return
        current = inspect.currentframe()
        if parents: self.get_parents(current)
        self.true_debug(current, objects, locale)
    def true_debug(self, current, objects, locale):
        debug_string = 'Function: ' + str(inspect.getouterframes(current)[1][3])
        #if locale == 'all': print inspect.getouterframes(current)[4]; return
        if objects != None: debug_string += ' Objects: ' + str(objects)
        if locale: debug_string += ' File: ' + str(inspect.getouterframes(current)[1][1])
        print debug_string
        return
    def get_parents(self, current):
        debug_string = 'Function: ' + str(inspect.getouterframes(current)[1][3]) + ' Parents:'
        family = list(inspect.getouterframes(current))
        for parent in family:
            debug_string += ' ' + str(parent[4])
        print debug_string
        return
#debug = TrueDebug

"""
Celery scheduler that runs tasks at startup immediately then continues with their
original plan.
"""
from djcelery import schedulers


class ImmediateFirstEntry( schedulers.ModelEntry ):
    def is_due( self ):
        if self.last_run_at is None:
            return True, 0
        return super( ImmediateFirstEntry, self ).is_due()
    def _default_now( self ):
        return None


class CeleryBeatScheduler( schedulers.DatabaseScheduler ):
    Entry = ImmediateFirstEntry

"""
Decorators
"""

class conditional_decorator(object):
    """ Applies decorator dec if conditional condition is met """
    def __init__(self, condition, dec, *args, **kwargs):
        self.decorator = dec
        self.decorator_args = (args, kwargs)
        self.condition = condition

    def __call__(self, func):
       if not self.condition:
           # Return the function unchanged, not decorated.
           return func
       return self.decorator(func, *self.decorator_args[0], **self.decorator_args[1])


def statelazyproperty(func):
    """ A decorator for state-based lazy evaluation of properties """
    cache = {}
    def _get(self):
        state = self.__getstate__()
        try:
            v = cache[state]
            logging.debug("Cache hit %s", state)
            return v
        except KeyError:
            logging.debug("Cache miss %s", state)
            cache[state] = value = func( self )
            return value
    return property(_get)

"""
Cache
"""

class Memoize(object):
    """
    Cached function or property

    >>> import random
    >>> @CachedFunc( ttl=3 )
    >>> def cachefunc_tester( *args, **kwargs ):
    >>>     return random.randint( 0, 100 )

    """
    __name__ = "<unknown>"
    def __init__( self, func=None, ttl=300 ):
        self.ttl = ttl
        self.__set_func( func )
    def __set_func( self, func=None, doc=None ):
        if not func:
            return False
        self.func = func
        self.__doc__ = doc or self.func.__doc__
        self.__name__ = self.func.__name__
        self.__module__ = self.func.__module__
    def __call__( self, func=None, doc=None, *args, **kwargs ):
        if func:
            self.__set_func( func, doc )
            return self
        now = time.time()
        try:
            value, last_update = self._cache
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except ( KeyError, AttributeError ):
            value = self.func( *args, **kwargs )
            self._cache = ( value, now )
        return value
    def __get__( self, inst, owner ):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except ( KeyError, AttributeError ):
            value = self.func( inst )
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = ( value, now )
        return value
    def __repr__( self ):
        return "<@CachedFunc: '%s'>" % self.__name__


"""
General Utils
Safe to run with.
"""

class LazyDict( dict ):
    def __getattr__( self, attr ):
        if attr in self:
            return self[attr]
        else:
            #return super(LazyDict,self).__getattr__(attr)
            raise AttributeError, "'%s' object has no attribute '%s'" \
                % ( self.__class__.__name__, attr )

    def __setattr__( self, attr, value ):
        if hasattr( super( LazyDict, self ), attr ):
            raise AttributeError, "'%s' object already has attribute '%s'" \
                % ( self.__class__.__name__, attr )
        self[attr] = value


class FilterableDict( dict ):
    """ Filter dict contents by str(key), list(keys), dict(key=value) """

    def filter( self, *args, **kwargs ):
        """ Filter dict object contents by str(key), list(keys), dict(key=value) where contents are an object and dict(key=value) are matched on obj.data """
        items = self.iteritems()
        for filter in list( list( *args ) + [dict( **kwargs )] ):
            if not len( filter ) > 0:
                continue
            filter_type = str( type( filter ) )
            if filter_type == "<type 'str'>":
                items = [( k, v ) for ( k, v ) in items if k == filter]
            elif filter_type == "<type 'list'>":
                items = [( k, v ) for ( k, v ) in items if k in filter]
            elif filter_type == "<type 'dict'>":
                items = [ ( k, v ) for ( k, v ) in items
                            for ( kwk, kwv ) in kwargs.items()
                              if v.get( kwk ) == kwv ]
        new = self.__new__( self.__class__, *list( items ) )
        return new

def convert_bytes_to_human( n ):
    """ Utility to convert bytes to human readable (K/M/G/etc) """
    SYMBOLS = ( 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y' )
    PREFIX = {}
    for i, j in enumerate( SYMBOLS ):
        PREFIX[j] = 1 << ( i + 1 ) * 10

    for i in reversed( SYMBOLS ):
        if n >= PREFIX[i]:
            value = float( n ) / PREFIX[i]
            return '%.1f%s' % ( value, i )

def convert_human_to_bytes( s ):
    """ Utility to convert human readable (K/M/G/etc) to bytes """
    SYMBOLS = ( 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y' )
    PREFIX = {}
    for i, j in enumerate( SYMBOLS ):
        PREFIX[j] = 1 << ( i + 1 ) * 10

    s = str( s ).upper()
    for i in SYMBOLS:
        if s.endswith( i ):
            return '%.0f' % ( float( s[:-1] ) * PREFIX[i] )

    # Must be bytes or invalid data
    #TODO What if it's invalid data? How should that be handled?
    return '%.0f' % float( s )


KEYNOTFOUND = '<KEYNOTFOUND>'       # KeyNotFound for dictDiff

def dict_diff( first, second ):
    """ Return a dict of keys that differ with another config object.  If a value is
        not found in one fo the configs, it will be represented by KEYNOTFOUND.
        @param first:   Fist dictionary to diff.
        @param second:  Second dicationary to diff.
        @return diff:   Dict of Key => (first.val, second.val)
    """
    diff = {}
    # Check all keys in first dict
    for key in first.keys():
        if ( not second.has_key( key ) ):
            diff[key] = ( first[key], KEYNOTFOUND )
        elif ( first[key] != second[key] ):
            diff[key] = ( first[key], second[key] )
    # Check all keys in second dict to find missing
    for key in second.keys():
        if ( not first.has_key( key ) ):
            diff[key] = ( KEYNOTFOUND, second[key] )
    return diff


#class LazyJSONEncoder(simplejson.JSONEncoder):
#    """ a JSONEncoder subclass that handle querysets and models objects. Add
#    your code about how to handle your type of object here to use when dumping
#    json """
#    def default(self,o):
#        # this handles querysets and other iterable types
#        try:
#            iterable = iter(o)
#        except TypeError:
#            pass
#        else:
#            return list(iterable)
#
#        # this handlers Models
#        try:
#            isinstance(o.__class__,ModelBase)
#        except Exception:
#            pass
#        else:
#            return force_unicode(o)
#
#        return super(LazyJSONEncoder,self).default(obj)


#def serialize_to_json(obj,*args,**kwargs):
#    """ A wrapper for simplejson.dumps with defaults as:
#
#    ensure_ascii=False
#    cls=LazyJSONEncoder
#
#    All arguments can be added via kwargs """
#    kwargs['ensure_ascii'] = kwargs.get('ensure_ascii',False)
#    kwargs['cls'] = kwargs.get('cls',LazyJSONEncoder)
#
#    return simplejson.dumps(obj,*args,**kwargs)


def qdct_as_kwargs( qdct ):
    kwargs = {}
    for k, v in qdct.items():
        kwargs[str( k )] = v
    return kwargs


