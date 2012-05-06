#!/usr/bin/env python

import os, sys
import time, datetime, logging
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import FilterableDict
#from heapq import merge

_paths = {'zfs':    "/usr/sbin/zfs",
         'zpool':  "/usr/sbin/zpool", }

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



class Pools(FilterableDict):
    def __new__(cls):
        self = super(Pools, cls).__new__(cls)
        self._raw_real = [self._zpool_list, [], {}]
        # Start with fresh data
        self.objects
        return self
    def __init__(self, *args, **kwargs):
        super(Pools, self).__init__(self, *args, **kwargs)

    @CachedFunc(ttl=60)
    def raw(self, *args, **kwargs):
        raw = self._raw_real[0](*self._raw_real[1], **self._raw_real[2])
        # Clear cache so any other functions will not get stale data
        self._cache = {}
        return raw

    @CachedFunc(ttl=60)
    def objects(self):
        # Generate objects from raw
        raw = self.raw
        objects = FilterableDict([ (name, Pool(**obj)) for name, obj in raw.iteritems() ])
        #objects = FilterableDict(raw)
        # {{{ FIXME This is not thread safe without locks
        self.clear()
        self.update(objects)
        # FIXME }}}
        return objects

    def __getitem__(self, arg):
        if arg in self.objects:
            return self._objects[arg]
        raise Exception, AttributeError
        #return super(Pools, self).__getitem__(arg)


    def _zpool(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(_paths['zpool']+' '+args[0], *args[1:])

    def _zpool_list(self, *pools, **kwargs):
        print "raw self=%s args=%s kwargs=%s" % (self, pools, kwargs)

        """ Utility to get a list of zfs pools and associated properties.
        Also aggregates parent/children information """

        args = ['list', '-H']

        kwargs['props'] = kwargs.get('props',
                          ['name','allocated','capacity','dedupratio','free','guid','health',
                          'size','altroot','ashift','autoexpand','autoreplace','bootfs',
                          'cachefile','dedupditto','delegation','failmode','listsnapshots',
                          'readonly','version'] )
        args.extend(['-o', ','.join(kwargs['props'])])

        if len(pools) > 0:
            args.extend(pools)

        cmdf = []
        for i in args:
            cmdf.append('{}')

        pool_list = {}
        for i in run(self._zpool(' '.join(cmdf), *args)):
            i = str(str(i).rstrip('\\n')).split("\t")
            d = {}

            for j_count,j in enumerate(kwargs['props']):
                v = i[j_count]

                ## Booleanize
                for k in ['autoexpand', 'autoreplace', 'delegation', 'listsnapshots', 'readonly']:
                    if j == k:
                        if v == "on":
                            v = True
                        elif v == "off":
                            v = False

                d[j] = v

            pool_list[d['name']] = d
        return pool_list




class DictWatch(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        print 'GET', key
        return val

    def __setitem__(self, key, val):
        print 'SET', key, val
        dict.__setitem__(self, key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        print 'update', args, kwargs
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

class zfs_obj(FilterableDict):
    def __init__(self, *args, **kwargs):
        if len(kwargs) == 1 and 'name' in kwargs:
            kwargs = self.lookup(kwargs.get(name))
        super(zfs_obj, self).__init__(*args, **kwargs)
    def __getattribute__(self, arg):
        try:
            return super(zfs_obj, self).__getattribute__('data')[arg]
        except (AttributeError):
            return super(zfs_obj, self).__getattribute__(arg)



class Pool(FilterableDict):
    """ Pool object """
    def __init__(self, lookup=None, **kwargs):
        #if lookup:
        #    kwargs = Pools.get(lookup)
        self.name = kwargs['name']
        self.update(kwargs)
    def __new__(cls, *args, **kwargs):
        return super(Pool, cls).__new__(cls, *args, **kwargs)
    idumps   = lambda self: `self`
    __str__ = lambda self: self.dumps()

class Dataset(FilterableDict):
    """ Dataset object """
    def __init__(self, lookup=None, **kwargs):
        #if lookup:
        #    kwargs = Pools.get(lookup)
        self.dataset_type = self
        self.name = kwargs['name']
        self.update(kwargs)
    def __new__(cls, *args, **kwargs):
        for subclass in zfs.dataset.__subclasses__():
            if subclass._type == kwargs['type']:
                return super(cls, subclass).__new__(subclass, *args, **kwargs)
        raise Exception, 'Dataset type not supported'
    idumps   = lambda self: `self`
    __str__ = lambda self: self.dumps()

class Filesystem(dataset):
    """ Filesystem object """
    def __new__(cls, *args, **kwargs):
        return super(Fileystem, cls).__new__(cls, *args, **kwargs)

class Snapshot(dataset):
    """ Snapshot object """
    def __new__(cls, *args, **kwargs):
        return super(Snapshot, cls).__new__(cls, *args, **kwargs)







class _CachedZFSObjList(FilterableDict):
    _raw_real = None
    def __new__(cls, func=None, args=[], **kwargs):
        self = super(_CachedZFSObjList, cls).__new__(cls)
        if func:
            self._raw_real = func
            self._raw_args = args
            self._raw_kwargs = kwargs
        return self

    #def _raw(self, *args, **kwargs):
    #    print "raw self=%s args=%s kwargs=%s" % (self, args, kwargs)
    #    return dict( self._raw[0]( self._raw[1] ) )

    #@CachedFunc(ttl=60)
    #def objects(self):
    #    return [ (k,v) for (k,v) in self._raw.iteritems() ]

class Datasets(_CachedZFSObjList):
    def __new__(cls):
        self = super(Datasets, cls).__new__(cls)
        self._raw = (self._zfs_list, None)
        return self

    def _zfs(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(_paths['zfs']+' '+args[0], *args[1:])

    def _zfs_list(self, *datasets, **kwargs):
        """ Utility to get a list of zfs volumes and associated properties.
        Also aggregates parent/children information """

        args = ['list', '-H', '-t', kwargs.get('type', 'all')]

        if kwargs.has_key('depth'):
            args.extend([ '-d', str(kwargs['depth']) ])

        kwargs['props'] = kwargs.get('props', ['name', 'type', 'used', 'available', 'creation', 'referenced',
                     'compressratio', 'mounted', 'quota', 'reservation', 'recordsize',
                     'mountpoint', 'sharenfs', 'checksum', 'compression', 'atime',
                     'devices', 'exec', 'setuid', 'readonly', 'zoned', 'snapdir',
                     'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only',
                     'normalization', 'casesensitivity', 'vscan', 'nbmand', 'sharesmb',
                     'refquota', 'refreservation', 'primarycache', 'secondarycache',
                     'usedbysnapshots', 'usedbydataset', 'usedbychildren',
                     'usedbyrefreservation', 'logbias', 'dedup', 'mlslabel', 'sync',
                     'refcompressratio'])
        args.extend(['-o', ','.join(kwargs['props'])])

        if len(datasets) > 0:
            args.append(datasets[0])

        cmdf = []
        for i in args:
            cmdf.append('{}')

        dataset_list = {}
        for i in run(self._zfs(' '.join(cmdf), *args)):
            i = str(str(i).rstrip('\\n')).split("\t")
            d = {}

            for j_count,j in enumerate(kwargs['props']):
                v = i[j_count]

                ## Booleanize
                if j == 'mounted':
                    if v == 'yes':
                        v = True
                    elif v == 'no' or v == '-':
                        v = False
                elif j == 'defer_destroy' or j == 'atime' or j == 'devices' or j == 'exec' or j == 'nbmand' or \
                   j == 'readonly' or j == 'setuid' or j == 'shareiscsi' or j == 'vscan' or j == 'xattr' or \
                   j == 'zoned' or j == 'utf8only':
                    if v == "on":
                        v = True
                    elif v == "off" or v == '-':
                        v = False
                ## Nullize
                elif v == '-':
                    if j == 'copies' or v == 'version':
                        v = 0
                    else:
                        v = ''

                d[j] = v

            dataset_list[d['name']] = d

        for d in dataset_list:
            d = dataset_list[d]

            (d['parent'], d['basename']) = os.path.split(d['name'])

            if len(d['basename']) <= 0 or len(d['parent']) <= 0:
                continue

            if dataset_list.has_key(d['parent']):
                if not dataset_list[d['parent']].has_key('children'):
                    dataset_list[d['parent']]['children'] = []
                dataset_list[d['parent']]['children'].append(d['name'])
        return dataset_list



#@cached(ttl=300)



class pool2(zfs_obj):
    """ Pool object """
    #def __init__(self, *args, **kwargs):
    #    super(pool2, self).__init__(*args, **kwargs)

class pool(FilterableDict):
    """ Pool object """
    def __init__(self, *args, **kwargs):
        self.name = args
        self.data = kwargs
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls, *args, **kwargs)

class dataset(FilterableDict):
    """ Dataset object """
    def __init__(self, *args, **kwargs):
        self.dataset_type = self
        self.name = args
        self.data = kwargs
    def __new__(cls, *args, **kwargs):
        for subclass in zfs.dataset.__subclasses__():
            if subclass._type == kwargs['type']:
                return super(cls, subclass).__new__(subclass, *args, **kwargs)
        raise Exception, 'Dataset type not supported'
    #idumps   = lambda self: `self`
    #__str__ = lambda self: self.dumps()

class filesystem(dataset):
    """ Filesystem object """
    _type='filesystem'
    def __new__(cls, *args, **kwargs):
        return zfs.dataset.__new__(cls, *args, **kwargs)

class snapshot(dataset):
    """ Snapshot object """
    _type='snapshot'
    def __new__(cls, *args, **kwargs):
        return zfs.dataset.__new__(cls, *args, **kwargs)



class zfs(object):
    """ Wrapper around zfs/zpool commands """

    def __new__(cls, *pools, **kwargs):
        self = super(zfs, cls).__new__(cls)
        self.data = kwargs

        return self

    def __objects(self, __object_name, __object_func, __object_class, *args, **kwargs):
        if not __object_name+'_raw' in self.data:
            self.data[__object_name+'_raw'] = FilterableDict(__object_func())
            self.data[__object_name] = FilterableDict([(k, __object_class(**v)) for (k,v) in self.data[__object_name+'_raw'].iteritems()])
        return self.data[__object_name].filter(*args, **kwargs)

    def pools(self, *args, **kwargs):
        return self.__objects('pools', self.__zpool_list, zfs.pool, *args, **kwargs)

    def datasets(self, *args, **kwargs):
        return self.__objects('datasets', self.__zfs_list, zfs.dataset, *args, **kwargs)

    def filesystems(self, *args, **kwargs):
        return self.datasets(*args, **dict(kwargs.items() + [('type', 'filesystem')] ))

    def snapshots(self, *args, **kwargs):
        return self.datasets(*args, **dict(kwargs.items() + [('type', 'snapshot')] ))

    def snapshot(self, *datasets, **kwargs):
        """ Creates snapshot(s) on *args
            zfs.snapshot(*datasets, recursive=[False]), name=[auto-%F_%T]) """

        if not len(datasets) > 0:
            ##TODO Figure out how to do exceptions
            return False

        # Default snapshot name
        kwargs['name'] = kwargs.get('name', datetime.datetime.now().strftime('auto-%F_%T'))

        if kwargs.get('recursive', False) == True:
            kwargs['recursive'] = '-r'
        else:
            kwargs['recursive'] = None

        logging.info('Creating snapshot on %s with %s', datasets, kwargs)
        for d in datasets:
            return self.__zfs('{} {} {}', 'snapshot', kwargs['recursive'], d+'@'+kwargs['name'])

    def __zpool_list(self, *pools, **kwargs):
            """ Utility to get a list of zfs pools and associated properties.
            Also aggregates parent/children information """

            args = ['list', '-H']

            kwargs['props'] = kwargs.get('props',
                              ['name','allocated','capacity','dedupratio','free','guid','health',
                              'size','altroot','ashift','autoexpand','autoreplace','bootfs',
                              'cachefile','dedupditto','delegation','failmode','listsnapshots',
                              'readonly','version'] )
            args.extend(['-o', ','.join(kwargs['props'])])

            if len(pools) > 0:
                args.extend(pools)

            cmdf = []
            for i in args:
                cmdf.append('{}')

            pool_list = {}
            for i in run(self.__zpool(' '.join(cmdf), *args)):
                i = str(str(i).rstrip('\\n')).split("\t")
                d = {}

                for j_count,j in enumerate(kwargs['props']):
                    v = i[j_count]

                    ## Booleanize
                    for k in ['autoexpand', 'autoreplace', 'delegation', 'listsnapshots', 'readonly']:
                        if j == k:
                            if v == "on":
                                v = True
                            elif v == "off":
                                v = False

                    d[j] = v

                pool_list[d['name']] = d
            return pool_list

    def __zpool_iostat(self, *pools, **kwargs):
        """ Utility to return zpool iostats on the specified pools """

        capture_length = kwargs.get('capture_length', 30)
        args = ['iostat', '-Tu']

        if len(pools) > 0:
            args.extend(pools)
        if int(capture_length) > 0:
            args.extend([str(capture_length), str(2)])

        cmdf = []
        for i in args:
            cmdf.append('{}')

        pool_iostat = {}
        timestamp = 0
        skip = 1000
        for (x,i) in enumerate(run(self.__zpool(' '.join(cmdf), *args))):
            if i.startswith('-----'):
                skip = x - 1
            if x < skip:
                continue
            i = ' '.join( str( str(i).rstrip('\\n')).split() )

            if i.isdigit():
                timestamp = datetime.datetime.fromtimestamp(int(i))
                continue
            if timestamp == 0:
                continue
            j = { 'timestamp': timestamp }

            try:
                (j['name'], j['alloc'], j['free'], j['iops_read'], j['iops_write'], j['bandwidth_read'],
                 j['bandwidth_write']) = i.split()
                pool_iostat[j['name']] = j
            except:
                continue
        return pool_iostat


