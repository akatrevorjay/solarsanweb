# -*- coding: utf-8 -*-

from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.db.models.base import ModelBase

import string, os, sys, logging, datetime

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

