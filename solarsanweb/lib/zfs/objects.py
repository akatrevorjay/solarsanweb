""""
$ zfs/class_hell.py -- Interface to zfs command line utilities (class based)
~ Trevor Joynson (aka trevorj) <trevorj@localhostsolutions.com>
"""

import os, sys
import time, datetime, logging
from django.utils import timezone
from iterpipes import run, cmd, linecmd, check_call, format
from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes

from .common import Error, NotImplemented
import pool, dataset, cmd, common

"""
Base
"""

class zfsBase( object ):
    """ Base class """
    _zfs_type = 'base'

    def __init__(self, name, *args, **kwargs):
        """ Initialize """
        self.name = name
        self.props = Properties(self)

    def __new__(cls, *args, **kwargs):
        return super(zfsBase, cls).__new__(cls, *args, **kwargs)

    def __repr__(self):
        name = getattr(self, 'name', None)
        return "%s('%s')" % (type(self).__name__, name)

    idumps  = lambda self: `self`
    __str__ = lambda self: self.dumps()

    def path( self, start=0, len=None ):
        """ Splits name of object into paths starting at index start """
        return self.name.split( '/' )[start:len]

    #@property
    def exists(self):
        try:
            name = self._get_prop('name')
            return True
        except:
            return False


class Properties(object):
    def __init__(self, parent):
        self.parent = parent
    def __getattribute__(self, attr):
        if attr == 'parent':
            return super(Properties, self).__getattribute__(attr)
        elif attr in self.parent._props:
            return self.parent._get_prop(attr)
        elif attr == 'all':
            return self.parent._get_prop(*self.parent._props)
        else:
            return super(Properties, self).__getattribute__(attr)
    def __call__(self):
        return self.parent._props



"""
Pool Handling
"""

class Pool( zfsBase ):
    """ Pool class """
    _zfs_type = 'pool'
    _props = ['name', 'allocated','capacity','dedupratio','free','guid','health',
              'size','altroot','ashift','autoexpand','autoreplace','bootfs',
              'cachefile','dedupditto','delegation','failmode','listsnapshots',
              'readonly','version']

    #def __init__(self, name, *args, **kwargs):
    #    super(Pool, self).__init__(name, *args, **kwargs)

    def _get_prop(self, *args):
        props = pool.list(self.name, props=list(args))[self.name]
        if len(args) == 1:
            return props[args[0]]
        else:
            return props

    @property
    def filesystem( self ):
        """ Returns the matching Filesystem for this Pool """
        return Filesystem(self.name)

class Dataset( zfsBase ):
    """ Dataset class """
    _zfs_type = 'dataset'
    _props = ['name', 'setuid', 'referenced', 'zoned', 'primarycache', 'logbias', 'creation', 'sync', 'dedup', 'sharenfs', 'usedbyrefreservation', 'sharesmb', 'canmount', 'mountpoint', 'casesensitivity', 'utf8only', 'xattr', 'mounted', 'compression', 'usedbysnapshots', 'copies', 'aclinherit', 'compressratio', 'readonly', 'version', 'normalization', 'type', 'secondarycache', 'refreservation', 'available', 'used', 'Exec', 'refquota', 'refcompressratio', 'quota', 'vscan', 'reservation', 'atime', 'recordsize', 'usedbychildren', 'usedbydataset', 'mlslabel', 'checksum', 'devices', 'nbmand', 'snapdir']

    #def __init__(self, name, *args, **kwargs):
    #    super(Dataset, self).__init__(name, *args, **kwargs)

    def __new__(cls, *args, **kwargs):
        if 'type' in kwargs:
            for subclass in Dataset.__subclasses__():
                if subclass._zfs_type == kwargs['type']:
                    return super(Dataset, cls).__new__(subclass, *args, **kwargs)
            raise Exception, 'Dataset type not supported'
        return super(Dataset, cls).__new__(cls, *args, **kwargs)

    def _get_prop(self, *args):
        props = dataset.list(self.name, type=self._zfs_type, props=list(args))[self.name]
        if len(args) == 1:
            return props[args[0]]
        else:
            return props

    @property
    def pool( self ):
        """ Returns the matching Pool for this Filesystem """
        return Pool(self.path(0, 1))

    @property
    def parent(self):
        path = self.path()
        if len(path) == 1:
            return None
        return Dataset('/'.join(path[:-1]))

class SnapshottableDataset(object):
    #@property
    def snapshots(self, **kwargs):
        """ Lists snapshots of this dataset """
        kwargs['type'] = 'snapshot'
        return self.children(**kwargs)

    #@property
    def filesystems(self, **kwargs):
        kwargs['type'] = 'filesystem'
        return self.children(**kwargs)

    #@property
    def children(self, **kwargs):
        datasets = dataset.list(self.name, type=kwargs.get('type', 'all'), prop=['name', 'type'], depth=kwargs.get('depth', 1))
        return [(Dataset(ds, type=datasets[ds]['type'])) for ds in datasets.keys()]

    #def snapshot( self, snapshot_name, **kwargs ):
    #    """ Snapshot this dataset """
    #    raise Exception('Not Implemented')


class Filesystem( Dataset, SnapshottableDataset ):
    _zfs_type = 'filesystem'
    """ Filesystem """
    pass

class Volume( Dataset, SnapshottableDataset ):
    _zfs_type = 'volume'
    """ Volume """
    pass

class Snapshot( Dataset ):
    _zfs_type = 'snapshot'
    """ Filesystem snapshot """

    @property
    def snapshot_name( self ):
        """ Returns the snapshot name """
        return self.basename.rsplit( '@', 1 )[1]

    @property
    def filesystem_name( self ):
        """ Returns the associated filesystem/volume name """
        return self.basename.rsplit( '@', 1 )[0]

    @property
    def filesystem( self ):
        """ Returns the associated filesystem for this snapshot """
        return Filesystem(self.filesystem_name)





