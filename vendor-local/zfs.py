#!/usr/bin/env python

import os, sys
import datetime, logging
from iterpipes import run, cmd, linecmd, check_call, format

## {{ zfs
class zfs(object):
    """ Wrapper around zfs/zpool commands """

    __paths = {
        'zfs': "/usr/sbin/zfs",
        'zpool': "/usr/sbin/zpool",
    }

    def __init__(self, *pools, **kwargs):
        self.data = kwargs
        self.pool = pool
        self.dataset = dataset

    def load(self):
        self.data['pools'] = self.pool.list()
        self.data['datasets'] = self.dataset.list()

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
            return call(zfs.__zfs('{} {} {}', 'snapshot', kwargs['recursive'], d+'@'+kwargs['name']))

    def __zfs(*args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(zfs._zfs__paths['zfs']+' '+args[0], *args[1:])
    __zfs = staticmethod(__zfs)

    def __zpool(*args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(zfs._zfs__paths['zpool']+' '+args[0], *args[1:])
    __zpool = staticmethod(__zpool)
## }}

## {{ zpool
class pool(object):
    """ Pool object """

    def __init__(self, name, **kwargs):
        self.name = name
        self.dataset = dataset
        self.data = kwargs

    def list(*pools, **kwargs):
            """ Utility to get a list of zfs volumes and associated properties.
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
            for i in run(zfs._zfs__zpool(' '.join(cmdf), *args)):
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
    list = staticmethod(list)

    def iostat(capture_length=30, *pools, **kwargs):
        """ Utility to return zpool iostats on the specified pools """

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
        for (x,i) in enumerate(run(zfs._zfs__zpool(' '.join(cmdf), *args))):
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
    iostat = staticmethod(iostat)
## }}

## {{ dataset
class dataset(object):
    """ Dataset object """

    def __init__(self, name, **kwargs):
        self.type = self
        self.name = name
        self.data = kwargs
        #self.list = None

    def snapshot(self, **kwargs):
        """ Creates snapshot on zfs.dataset object.
            zfs.dataset.snapshot(**kwargs) """
        return super(zfs, self).snapshot(self.name, **kwargs)

    def list(*datasets, **kwargs):
        """ Utility to get a list of zfs volumes and associated properties.
        Also aggregates parent/children information """

        args = ['list', '-H', '-t', kwargs.get('type', 'filesystem')]

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
        for i in run(zfs._zfs__zfs(' '.join(cmdf), *args)):
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
    list = staticmethod(list)
## }}

## {{ snapshot
class snapshot(dataset):
    """ Snapshot object (Snapshots are actually Datasets) """

    def __init__(self, name, **kwargs):
        super(Dataset, self).method(*args, **kwargs)
        # Snapshots can't make snapshots
        #self.snapshot = None
## }}


