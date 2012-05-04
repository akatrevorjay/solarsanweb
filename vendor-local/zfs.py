#!/usr/bin/env python

import os, sys
import datetime, logging
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import filterdictsofdicts, filterarrayofdicts

class zfs(object):
    """ Wrapper around zfs/zpool commands """

    __paths = {
        'zfs': "/usr/sbin/zfs",
        'zpool': "/usr/sbin/zpool",
    }

    def __init__(self, *pools, **kwargs):
        self.data = kwargs

    def pools(self, *args, **kwargs):
        if not 'pools' in self.data:
            self.data['pools'] = self.__zpool_list()

        if len(kwargs.keys()) > 0:
            pools_all = filterdictsofdicts(self.data['pools'], **kwargs)
        else:
            pools_all = self.data['pools']

        if len(args) > 0:
            pools = {}
            for i in args:
                if i in pools:
                    pools[i] = pools_all[i]
        else:
            pools = pools_all

        return pools

    def datasets(self, *args, **kwargs):
        if not 'datasets' in self.data:
            self.data['datasets'] = self.__zfs_list()

        if len(kwargs.keys()) > 0:
            datasets_all = filterdictsofdicts(self.data['datasets'], **kwargs)
        else:
            datasets_all = self.data['datasets']

        if len(args) > 0:
            datasets = {}
            for i in args:
                if i in datasets_all:
                    datasets[i] = datasets_all[i]
        else:
            datasets = datasets_all

        return datasets

    def filesystems(self, *args, **kwargs):
        kwargs['type'] = 'filesystem'
        return self.datasets(*args, **kwargs)

    def snapshots(self, *args, **kwargs):
        kwargs['type'] = 'snapshot'
        return self.datasets(*args, **kwargs)

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

    def __zfs(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(self._zfs__paths['zfs']+' '+args[0], *args[1:])

    def __zpool(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(self._zfs__paths['zpool']+' '+args[0], *args[1:])

    def __zfs_list(self, *datasets, **kwargs):
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
        for i in run(self.__zfs(' '.join(cmdf), *args)):
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

    class pool(object):
        """ Pool object """

        def __init__(self, name, **kwargs):
            self.name = name
            self.dataset = dataset
            self.data = kwargs


    class dataset(object):
        """ Dataset object """

        def __init__(self, name, **kwargs):
            self.type = self
            self.name = name
            self.data = kwargs


    class filesystem(dataset):
        """ Filesystem object """


    class snapshot(dataset):
        """ Snapshot object """


