# -*- coding: utf-8 -*-

from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.db.models.base import ModelBase

from solarsan.models import Pool, Dataset
import string, os, sys, logging, datetime

def graph_stats(count=1):
    """ Gets graph stats """
    graph = {}

    for p in Pool.objects.all():
        iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
        #iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
        
        graph[p.name] = {}

        total = int(iostats[0].alloc + iostats[0].free)
        graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

        graph[p.name]['graph_iops'] = {'values': [[], []]}
        graph[p.name]['graph_throughput'] = {'values': [[], []]}
        for iostat in iostats:
            graph[p.name]['graph_iops']['values'][0].insert(0, int(iostat.iops_read))
            graph[p.name]['graph_iops']['values'][1].insert(0, int(iostat.iops_write))
            graph[p.name]['graph_throughput']['values'][0].insert(0, int(iostat.bandwidth_read))
            graph[p.name]['graph_throughput']['values'][1].insert(0, int(iostat.bandwidth_write))
    return graph

#def pool_utilization():
#    graph = {}
#
#    for p in Pool.objects.all():
#        #iostats = p.pool_iostat_set.order_by('timestamp')[:count:offset]
#        iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
#        
#        graph[p.name] = {}
#
#        total = int(iostats[0].alloc + iostats[0].free)
#        graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }
#
#    return graph

def zfs_snapshot(*datasets, **kwargs):
    """ Utility to create snapshots """
    
    kwargs['name'] = kwargs.get('name', datetime.datetime.now().strftime('auto-%F_%T'))

    if not len(datasets) > 0:
        datasets = []
        for p in Pool.objects.all():
            datasets.append(str(p.name))

    args = ''
    recursive_debug_out = ''
    if kwargs.get('recursive', True) == True:
        args+=' -r'
        recursive_debug_out = "recursive "
    
    logging.info('Creating %ssnapshot "%s" on %s', recursive_debug_out, kwargs['name'], datasets)
    for d in datasets:
        os.popen('/usr/sbin/zfs snapshot '+args+' "'+d+'@'+kwargs['name']+'"').read()

def zpool_list(zfs_zpools='', opts=''):
    """ Utility to get a list of zfs volumes and associated properties.
    Also aggregates parent/children information """
    if len(zfs_zpools) == 0:
        zfs_zpools = []
    if len(opts) == 0:
        opts = {}
    args = ''
    
    if not opts.has_key('props'):
        opts['props'] = ['name','allocated','capacity','dedupratio','free','guid','health',
                         'size','altroot','ashift','autoexpand','autoreplace','bootfs',
                         'cachefile','dedupditto','delegation','failmode','listsnapshots',
                         'readonly','version']
    args += ' -o '+','.join(opts['props'])

    if len(zfs_zpools) > 0:
        args += " '"+ "' '".join(zfs_zpools) +"'"

    pools = {}
    
    zfs_list_out = str(os.popen('/usr/sbin/zpool list -H'+args).read()).splitlines()
    for i in zfs_list_out:
        i = str(i).split("\t")
        d = {}

        for j_count,j in enumerate(opts['props']):
            v = i[j_count]

            ## Booleanize
            if j == 'autoexpand' or j == 'autoreplace' or j == 'delegation' or j == 'listsnapshots' or j == 'readonly':
                if v == "on":
                    v = True
                elif v == "off":
                    v = False
            
            d[j] = v
        
        pools[d['name']] = d

    return pools

def zfs_list(opts=''):
    """ Utility to get a list of zfs volumes and associated properties.
    Also aggregates parent/children information """
    if len(opts) == 0:
        opts = {}

    args = ''
    
    if not opts.has_key('type'):
        opts['type']='filesystem'
    args += ' -t '+opts['type']

    if opts.has_key('depth'):
        args += ' -d '+str(opts['depth'])

    if not opts.has_key('props'):
        opts['props'] = ['name', 'type', 'used', 'available', 'creation', 'referenced',
                     'compressratio', 'mounted', 'quota', 'reservation', 'recordsize',
                     'mountpoint', 'sharenfs', 'checksum', 'compression', 'atime',
                     'devices', 'exec', 'setuid', 'readonly', 'zoned', 'snapdir',
                     'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only',
                     'normalization', 'casesensitivity', 'vscan', 'nbmand', 'sharesmb',
                     'refquota', 'refreservation', 'primarycache', 'secondarycache',
                     'usedbysnapshots', 'usedbydataset', 'usedbychildren',
                     'usedbyrefreservation', 'logbias', 'dedup', 'mlslabel', 'sync',
                     'refcompressratio']
    args += ' -o '+','.join(opts['props'])

    if opts.has_key('dataset'):
        args += ' '+opts['dataset']

    datasets = {}
    
    zfs_list_out = str(os.popen('/usr/sbin/zfs list -H'+args).read()).splitlines()
    for i in zfs_list_out:
        i = str(i).split("\t")
        d = {}

        for j_count,j in enumerate(opts['props']):
            v = i[j_count]
            
            ## Booleanize
            if j == 'mounted':
                if v == 'yes':
                    v = True
                elif v == 'no':
                    v = False
            if j == 'defer_destroy' or j == 'atime' or j == 'devices' or j == 'exec' or j == 'nbmand' or \
               j == 'readonly' or j == 'setuid' or j == 'shareiscsi' or j == 'vscan' or j == 'xattr' or \
               j == 'zoned' or j == 'utf8only':
                if v == "on":
                    v = True
                elif v == "off":
                    v = False
            
            d[j] = v
        
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

def zpool_iostat(capture_length=2, zfs_zpools=''):
    """ Utility to return zpool iostat on the specified zpools """
    args = ''
    if len(zfs_zpools) > 0:
        args += " '"+ "' '".join(zfs_zpools) +"'"
    iostats = {}
    for line in str(os.popen('/usr/sbin/zpool iostat '+args+' '+str(capture_length)+' 2 | tail -n +5').read()).splitlines():
        i = {}
        (i['name'], i['alloc'], i['free'], i['iops_read'], i['iops_write'], i['bandwidth_read'], i['bandwidth_write']) = line.split()
        iostats[i['name']] = i
    return iostats

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
