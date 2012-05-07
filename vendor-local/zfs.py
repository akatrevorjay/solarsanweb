#!/usr/bin/env python

import os, sys
import time, datetime, logging
from django.utils import timezone
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import FilterableDict
from solarsanweb.solarsan.utils import convert_bytes_to_human, convert_human_to_bytes

_paths = {'zfs':    "/usr/sbin/zfs",
          'zpool':  "/usr/sbin/zpool", }

#
# TODO Convert to/from bytes/human here, before handing it off
#

class Pools(FilterableDict):
    ttl = 5

    def __new__(cls, *args, **kwargs):
        self = super(Pools, cls).__new__(cls, *args, **kwargs)
        self.refresh(*args, **kwargs)
        return self

    def __getitem__(self, arg):
        now = time.time()
        # FIXME TODO Caching is a problem when deleting because the task just re-adds the datasets...
        if now - self.timestamp > self.ttl:
            self.refresh()
        return super(Pools, self).__getitem__(arg)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def refresh(self, *args, **kwargs):
        now = time.time()
        if args:
            data = dict(args)
        elif kwargs:
            data = kwargs
        else:
            data = [ (name, Pool(**obj))
                for name, obj in self._zpool_list().items() ]
        # {{{ FIXME This is not thread safe without locks
        self.clear()
        self.update(data)
        self.timestamp = now
        # FIXME }}}

    def _zpool(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(_paths['zpool']+' '+args[0], *args[1:])

    def _zpool_list(self, *pools, **kwargs):
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

    def iostat(self, *pools, **kwargs):
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
        for (x,i) in enumerate(run(self._zpool(' '.join(cmdf), *args))):
            if i.startswith('-----'):
                skip = x - 1
            if x < skip:
                continue
            i = ' '.join( str( str(i).rstrip('\\n')).split() )

            if i.isdigit():
                timestamp = timezone.make_aware(
                        datetime.datetime.fromtimestamp(int(i)), timezone.get_current_timezone() )
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


#class zfs_obj(FilterableDict):
#    def __init__(self, *args, **kwargs):
#        if len(kwargs) == 1 and 'name' in kwargs:
#            kwargs = self.lookup(kwargs.get(name))
#        super(zfs_obj, self).__init__(*args, **kwargs)
#    def __getattribute__(self, arg):
#        try:
#            return super(zfs_obj, self).__getattribute__('data')[arg]
#        except (AttributeError):
#            return super(zfs_obj, self).__getattribute__(arg)


class Pool(FilterableDict):
    """ Pool object """
    def __init__(self, lookup=None, **kwargs):
        #if lookup:
        #    kwargs = Pools[lookup]
        self.name = kwargs['name']
        self.update(kwargs)
    def __new__(cls, *args, **kwargs):
        return super(Pool, cls).__new__(cls, *args, **kwargs)
    idumps   = lambda self: `self`
    __str__ = lambda self: self.dumps()
    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)


class Dataset(FilterableDict):
    """ Dataset object """
    def __init__(self, **kwargs):
        self.dataset_type = self
        self.name = kwargs['name']
        self.update(kwargs)

    def __new__(cls, *args, **kwargs):
        for subclass in Dataset.__subclasses__():
            if subclass.type == kwargs['type']:
                return super(Dataset, cls).__new__(subclass, *args, **kwargs)
        raise Exception, 'Dataset type not supported'

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def delete(self, **kwargs):
        """ (DANGEROUS) Delete dataset from filesystem """
        args = ['destroy']

        if kwargs.get('recursive', False) == True:
            args.append('-r')

        if not 'name' in self:
            logging.error("Delete was attemped on an empty ZFS object!")
            # TODO Better exceptions
            raise Exception
        args.append(self['name'])

        cmdf = []
        for i in args:
            cmdf.append('{}')

        # Should we catch the retval and raise an Exception on failure or is this fine?
        return check_call(self._zfs(' '.join(cmdf), *args))

    def _zfs(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(_paths['zfs']+' '+args[0], *args[1:])


class Filesystem(Dataset):
    """ Filesystem object """
    type='filesystem'

    def snapshot(self, **kwargs):
        """ Creates snapshot(s) on *datasets
            zfs.snapshot(*datasets, recursive=[False]), name=[auto-%F_%T]) """

        args = ['snapshot']

        if kwargs.get('recursive', False) == True:
            args.append('-r')

        # Default snapshot name
        kwargs['name'] = kwargs.get('name', timezone.now().strftime('auto-%F_%T'))

        args.append( self['name']+'@'+kwargs['name'] )

        cmdf = []
        for i in args:
            cmdf.append('{}')

        logging.info('Creating snapshot on %s with %s', self.name, kwargs)
        return check_call(self._zfs(' '.join(cmdf), *args))

class Snapshot(Dataset):
    """ Snapshot object """
    type='snapshot'



class Datasets(FilterableDict):
    ttl = 5

    def __new__(cls, *args, **kwargs):
        self = super(Datasets, cls).__new__(cls, *args, **kwargs)
        #print "cls=%s self=%s args=%s kwargs=%s" % (cls, self, args, kwargs)
        self.refresh(*args, **kwargs)
        return self

    def __getitem__(self, arg):
        now = time.time()
        # FIXME TODO Caching is a problem when deleting because the task just re-adds the datasets...
        if now - self.timestamp > self.ttl:
            self.refresh()
        return super(Datasets, self).__getitem__(arg)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def refresh(self, *args, **kwargs):
        now = time.time()
        if args:
            data = dict(args)
        elif kwargs:
            data = kwargs
        else:
            data = [ (name, Dataset(**obj))
                for name, obj in self._zfs_list().items() ]
        # {{{ FIXME This is not thread safe without locks
        self.clear()
        self.update(data)
        self.timestamp = now
        # FIXME }}}

    def _zfs(self, *args):
        """ Returns a linecmd with format args[0] and strings args[1:] """
        return linecmd(_paths['zfs']+' '+args[0], *args[1:])
    #_zfs = staticmethod(_zfs)

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

class _zfs(object):
    """ Wrapper around zfs/zpool commands """
    Pools = Pools()
    Datasets = Datasets()
    # TODO These too..
    #Filesystems =
    #Snapshots =
zfs = _zfs()

