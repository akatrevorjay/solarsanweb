
class FilterableDict(dict):
    """ Filter dict contents by str(key), list(keys), dict(key=value) """

    def filter(self, *args, **kwargs):
        """ Filter dict object contents by str(key), list(keys), dict(key=value) where contents are an object and dict(key=value) are matched on obj.data """
        #print "args = %s" % list(*args)
        #print "kwargs = %s" % dict(**kwargs)

        items = self.iteritems()
        #print "items before = %s" % FilterableDictOfObjs( list(items) )
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
                              if (str(type(v)) == "<type 'dict'>" and v.get(kwk) == kwv)
                                or (v.data[kwk] == kwv) ]
        #print "items = %s" % FilterableDictOfObjs(items)
        return FilterableDict(items)

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



## What follows below are from: http://wiki.python.org/moin/PythonDecoratorLibrary
## Along with MANY MANY more, remember it.

import functools

class memoized(object):
   ''' Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated). '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         value = self.func(*args)
         self.cache[args] = value
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)

import decorator

def _memoize(func, *args, **kw):
    if kw: # frozenset is used to ensure hashability
        key = args, frozenset(kw.iteritems())
    else:
        key = args
    cache = func.cache # attributed added by memoize
    if key in cache:
        return cache[key]
    else:
        cache[key] = result = func(*args, **kw)
        return result

def memoize(f):
    f.cache = {}
    return decorator.decorator([_memoize, f])

''' Examples
@memoized
def fibonacci(n):
   "Return the nth fibonacci number."
   if n in (0, 1):
      return n
   return fibonacci(n-1) + fibonacci(n-2)

print fibonacci(12)
'''

def simple_decorator(decorator):
    '''This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied.'''
    def new_decorator(f):
        g = decorator.decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

""" Examples
@simple_decorator
def my_simple_logging_decorator(func):
    def you_will_never_see_this_name(*args, **kwargs):
        print 'calling {}'.format(func.__name__)
        return func(*args, **kwargs)
    return you_will_never_see_this_name

@my_simple_logging_decorator
def double(x):
    'Doubles a number.'
    return 2 * x

assert double.__name__ == 'double'
assert double.__doc__ == 'Doubles a number'
print double(155)
"""



import sys

def propget(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(func, doc=func.__doc__)
    else:
        doc = prop.__doc__ or func.__doc__
        prop = property(func, prop.fset, prop.fdel, doc)
    return prop

def propset(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(None, func, doc=func.__doc__)
    else:
        doc = prop.__doc__ or func.__doc__
        prop = property(prop.fget, func, prop.fdel, doc)
    return prop

def propdel(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(None, None, func, doc=func.__doc__)
    else:
        prop = property(prop.fget, prop.fset, func, prop.__doc__)
    return prop

""" Example
class Example(object):

    @propget
    def myattr(self):
        return self._half * 2

    @propset
    def myattr(self, value):
        self._half = value / 2

    @propdel
    def myattr(self):
        del self._half


## Same as above but doesn't require new decorators
class Example(object):
    @apply
    def myattr():
                doc = '''This is the doc string.'''

        def fget(self):
                        return self._half * 2

        def fset(self, value):
                        self._half = value / 2

        def fdel(self):
                        del self._half

        return property(**locals())
"""

import time

class cached_property(object):
    ''' Decorator for read-only properties evaluated only once within TTL period.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)
o
    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]
    '''
    def __init__(self, ttl=300):
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value


import functools, inspect

def decorator(func):
    ''' Allow to use decorator either with arguments or not. '''

    def isFuncArg(*args, **kw):
        return len(args) == 1 and len(kw) == 0 and (
            inspect.isfunction(args[0]) or isinstance(args[0], type))

    if isinstance(func, type):
        def class_wrapper(*args, **kw):
            if isFuncArg(*args, **kw):
                return func()(*args, **kw) # create class before usage
            return func(*args, **kw)
        class_wrapper.__name__ = func.__name__
        class_wrapper.__module__ = func.__module__
        return class_wrapper

    @functools.wraps(func)
    def func_wrapper(*args, **kw):
        if isFuncArg(*args, **kw):
            return func(*args, **kw)

        def functor(userFunc):
            return func(userFunc, *args, **kw)

        return functor

    return func_wrapper

""" Example
@decorator
def apply(func, *args, **kw):
    return func(*args, **kw)

@decorator
class apply:
    def __init__(self, *args, **kw):
        self.args = args
        self.kw   = kw

    def __call__(self, func):
        return func(*self.args, **self.kw)

#
# Usage in both cases:
#
@apply
def test():
    return 'test'

assert test == 'test'

@apply(2, 3)
def test(a, b):
    return a + b

assert test is 5

Note: There is only one drawback: wrapper checks its arguments for single function or class. To avoid wrong behavior you can use keyword arguments instead of positional, e.g.:

Toggle line numbers

@decorator
def my_property(getter, *, setter=None, deleter=None, doc=None):
    return property(getter, setter, deleter, doc)
"""


import sys

class debug:
    '''Decorator which helps to control what aspects of a program to debug
    on per-function basis. Aspects are provided as list of arguments.
    It DOESN'T slowdown functions which aren't supposed to be debugged.
    '''
    def __init__(self, aspects=None):
        self.aspects = set(aspects)

    def __call__(self, f):
        if self.aspects & WHAT_TO_DEBUG:
            def newf(*args, **kwds):
                print >> sys.stderr, f.func_name, args, kwds
                f_result = f(*args, **kwds)
                print >> sys.stderr, f.func_name, "returned", f_result
                return f_result
            newf.__doc__ = f.__doc__
            return newf
        else:
            return f

""" Examples
WHAT_TO_DEBUG = set(['io', 'core'])  # change to what you need

@debug(['io'])
def prn(x):
    print x

@debug(['core'])
def mult(x, y):
    return x * y

prn(mult(2, 2))
"""



def addto(instance):
    """ Adds methods to class instance """
    def decorator(f):
        import types
        f = types.MethodType(f, instance, instance.__class__)
        setattr(instance, f.func_name, f)
        return f
    return decorator

""" Examples
class Foo:
    def __init__(self):
        self.x = 42

foo = Foo()

@addto(foo)
def print_x(self):
    print self.x

# foo.print_x() would print "42"
"""
















