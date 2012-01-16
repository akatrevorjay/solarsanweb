# -*- coding: utf-8 -*-

from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.db.models.base import ModelBase

import string, os, sys

def zfs_list(opts={}):
    """ Utility to get a list of zfs volumes and associated properties.
    Also aggregates parent/children information """
    
    args = ''
    
    if not opts.has_key('type'):
        opts['type']='filesystem'
    args += ' -t '+opts['type']

    if opts.has_key('depth'):
        args += ' -d '+str(opts['depth'])

    if opts.has_key('props'):
        zfs_props = opts['props']
    else:
        zfs_props = ['name', 'type', 'used', 'available', 'creation', 'referenced',
                     'compressratio', 'mounted', 'quota', 'reservation', 'recordsize',
                     'mountpoint', 'sharenfs', 'checksum', 'compression', 'atime',
                     'devices', 'exec', 'setuid', 'readonly', 'zoned', 'snapdir',
                     'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only',
                     'normalization', 'casesensitivity', 'vscan', 'nbmand', 'sharesmb',
                     'refquota', 'refreservation', 'primarycache', 'secondarycache',
                     'usedbysnapshots', 'usedbydataset', 'usedbychildren',
                     'usedbyrefreservation', 'logbias', 'dedup', 'mlslabel', 'sync',
                     'refcompressratio']
    args += ' -o '+','.join(zfs_props)

    if opts.has_key('dataset'):
        args += ' '+opts['dataset']

    datasets = {}
    
    zfs_list_out = str(os.popen('/usr/sbin/zfs list -H'+args).read()).splitlines()
    for i in zfs_list_out:
        i = str(i).split("\t")
        d = {}

        for j_count,j in enumerate(zfs_props):
            d[j] = i[j_count]
        
        datasets[d['name']] = d

    for d in datasets:
        d = datasets[d]
        
        (d['parent'], d['basename']) = os.path.split(d['name'])

        if len(d['basename']) <= 0 or len(d['parent']) <= 0:
            continue
        
        if not datasets[d['parent']].has_key('children'):
            datasets[d['parent']]['children'] = []
        datasets[d['parent']]['children'].append(d['name'])

    return datasets

def zpool_iostat(zpool, capture_length):
    """ Utility to return zpool iostat on the specified zpool """
    return str(os.popen('/usr/sbin/zpool iostat \''+zpool+'\' '+str(capture_length)+' 2 | tail -n +5').read()).split()



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


class LazyJSONEncoder(simplejson.JSONEncoder):
    """ a JSONEncoder subclass that handle querysets and models objects. Add
    your code about how to handle your type of object here to use when dumping
    json """
    def default(self,o):
        # this handles querysets and other iterable types
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)

        # this handlers Models
        try:
            isinstance(o.__class__,ModelBase)
        except Exception:
            pass
        else:
            return force_unicode(o)

        return super(LazyJSONEncoder,self).default(obj)

def serialize_to_json(obj,*args,**kwargs):
    """ A wrapper for simplejson.dumps with defaults as:

    ensure_ascii=False
    cls=LazyJSONEncoder

    All arguments can be added via kwargs
    """

    kwargs['ensure_ascii'] = kwargs.get('ensure_ascii',False)
    kwargs['cls'] = kwargs.get('cls',LazyJSONEncoder)


    return simplejson.dumps(obj,*args,**kwargs)

def qdct_as_kwargs(qdct):
    kwargs={}
    for k,v in qdct.items():
        kwargs[str(k)]=v
    return kwargs
