""""
$ zfs/class_hell.py -- Interface to zfs command line utilities (class based)
~ Trevor Joynson (aka trevorj) <trevorj@localhostsolutions.com>
"""

import os
import sys
import time
import datetime
import logging

import cmd
import common
import dataset
import models as z

from collections import defaultdict

from django.utils import timezone
from django.core import cache
from solarsan.utils import FilterableDict, CacheDict, convert_bytes_to_human, convert_human_to_bytes


"""
Base
"""


class BaseMixIn(object):
    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, getattr(self, 'name', None))
    def __unicode__(self):
        return self.name


ZFS_TYPE_MAP = {}


class zfsBaseCommon(object):
    """ Base common class """
    def __init__(self, *args, **kwargs):
        """ Initialize """
        # Replace list with the instance version
        #self.list = self._list_instance
        self._get_type = self._get_type_instance
        if 'name' in kwargs:
            self.name = kwargs['name']
        return super(zfsBaseCommon, self).__init__(*args, **kwargs)

    def clear(self):
        self.get()

    @property
    def props(self):
        """ Sets and returns Properties object """
        assert getattr(self, 'name', None)
        if not getattr(self, '_props', None):
            self._props = Properties(parent=self)
        return self._props

    @property
    def type(self):
        """ Returns ZFS object type string """
        return self.__class__.__name__.lower()

    @classmethod
    def _get_type_class(cls, name):
        return cls.ZFS_TYPE_MAP[name]
    def _get_type_instance(self, name):
        return self.ZFS_TYPE_MAP[name]
    _get_type = _get_type_class


    def path( self, start=0, len=None ):
        """ Splits name of object into paths starting at index start """
        return self.name.split( '/' )[start:len]

    def exists(self):
        """ Checks if object exists """
        # Check if type property is there, should always be there.
        try:
            self.list(self.name)
            if 'type' in self.props:
                return True
        except:
            return False

    @classmethod
    def list(cls, *args, **kwargs):
        zargs = ['list', '-H']
        self = kwargs.pop('self', None)
        get_type = self and self._get_type or cls._get_type
        skip = kwargs.get('skip', None)

        # Property selection
        props = kwargs.get('props', ['name'])
        if not isinstance(props, list):
            props = isinstance(props, basestring) and [props] or isinstance(props, tuple) and list(props)
        if not get_type('pool').__subclasscheck__(cls) and 'type' not in props:
            props += ['type']
        if not 'guid' in props:
            props.append('guid')
        zargs += ['-o', ','.join(props).lower(), ]
        # ZFS object selection (pool/dataset starting point for walking tree, etc)
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        zargs.extend(args)

        # Datasets (the zfs command in particular) have a better CLI interface, so allow for more control when it comes to those
        if get_type('pool').__subclasscheck__(cls):
            obj_type_default = 'pool'
        else:
            if kwargs.get('recursive') == True:
                zargs.append('-r')
            zargs.extend(['-t', kwargs.get('type', 'all')])
            if 'source' in kwargs:
                zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs:
                zargs.extend(['-d', str(int(kwargs['depth']))])
            obj_type_default = None

        # Prep vars, trying out an idea by keeping all objects per active dataset/pool referenced to here, that way they are all in sync (hopefully?)
        #objs = OBJ_TREE
        ret_type = kwargs.get('ret', dict)
        if ret_type == list:
            ret = []
        elif ret_type == dict:
            ret = {}
        else:
            raise Exception("Invalid return object type '%s' specified")

        # Generate command and execute, parse output
        for line in cls.zcmd(*zargs).splitlines():
            line = dict(zip(props == ['all'] and getattr(self, 'PROPS', None) or props,
                            str(line).rstrip("\n").split()))

            name = line['name']
            if skip and skip == name:
                continue

            obj_type = line.get('type', obj_type_default)
            obj_cls = cls.ZFS_TYPE_MAP[obj_type]
            #############
            ## HACKERY ##
            #############
            if getattr(obj_cls, '_fields', None):
                obj, created = obj_cls.objects.get_or_create(name=name, guid=line['guid'], auto_save=False)
            else:
                obj = obj_cls(name=name)
            if ret_type == dict:
                ret[name] = obj
            elif ret_type == list:
                ret.append(obj)

            #if not name in objs:
            #    objs[name] = {}
            #if obj_cls.__name__ not in objs[name]:
            #    o = cls(name=name)
            #    objs[name][o.__class__.__name__] = o
            #o = objs[name][obj_cls.__name__]
            #ret[name] = o

        return ret


class zfsBaseProps(object):
    @classmethod
    def get_default_prop_list(cls):
        """ Returns list of actual property names """
        return self.PROPS

    def get_prop_list(self):
        """ Returns list of default property names """
        raise NotImplementedError

    def get(self, *args, **kwargs):
        """ Returns requested properties *args with **kwargs opts for self """
        kwargs.update({'self': self,
                       'walk_only': [self.name], })
        return self._get(*args, **kwargs)

    def set(self, name, value, **kwargs):
        # Initial arguments
        args = ['set']
        # Options
        if kwargs.get('recursive'):
            args.append('-r')

        # Generate args & command
        args.extend(['%s=%s' % (str(name), str(value)), self.name])
        # Check for bad retval
        ret = self.zcmd(*args, ret=int)
        if ret > 0:
            raise Exception('set failed; retval=%s' % ret)

    @classmethod
    def _get(cls, *args, **kwargs):
        """ Returns requested properties *args with **kwargs opts """
        zargs = ['get']
        self = kwargs.pop('self', None)
        get_type = self and self._get_type or cls._get_type

         # Props
        args = args or ['all']
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)

        # Object[s] to start walking tree from
        walk_only = kwargs.get('walk_only', [])
        if not isinstance(walk_only, list):
            walk_only = isinstance(walk_only, basestring) and [walk_only] or isinstance(walk_only, tuple) and list(walk_only)

        # The zfs command has gotten a few interface tweaks over the years that give it en edge over zpool
        if get_type('pool').__subclasscheck__(cls):
            splitdelim = None
            if not walk_only:
                raise Exception('Cannot _get Pools without giving me a list (walk_only)')
        else:
            zargs.append('-H')
            splitdelim = "\t"
            if kwargs.get('recursive'):
                zargs.append('-r')
            if 'source' in kwargs:
                zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs:
                zargs.extend(['-d', int(kwargs['depth'])])
            zargs.extend(['-t', kwargs.get('type', 'all')])

        # Build prop list to grab
        zargs += [','.join(args).lower(), ]
        # Tack on what to walk_only if so
        if walk_only:
            zargs.extend(walk_only)

        # Prep vars, trying out an idea by keeping all objects per active dataset/pool referenced to here, that way they are all in sync (hopefully?)
        ret = defaultdict(dict)
        skip = 0
        for line in cls.zcmd(*zargs).splitlines():
            line = str(line).rstrip("\n")
            (obj_name, name, value, source) = line.split(splitdelim, 4)
            #ret[obj_name][name] = {'value': value, 'source': source}
            ret[obj_name][name] = get_type('property')(parent_name=obj_name, name=name, value=value, source=source)
            #if self and self.name == obj_name:
            #    ret[obj_name][name].parent = self
            #ret[obj_name][name] = get_type('property')(name=name, source=source, value=value)

        # If we're a dataset and recursive opt is set, return the full hash including dataset name as first key
        if not get_type('pool').__subclasscheck__(cls) and kwargs.get('recursive'):
            return ret

        # If we only requested a single property from a single object that isn't the magic word 'all', just return the value.
        if not kwargs.get('recursive') and len(args) == 1 and 'all' not in args:
            ret = ret[ret.keys()[0]]
        return ret[ret.keys()[0]]


#class zfsBase(SingletonMixIn):
class zfsBase(zfsBaseProps, zfsBaseCommon, BaseMixIn):
    ZFS_TYPE_MAP = ZFS_TYPE_MAP
    def __new__(cls, *args, **kwargs):
        #logging.debug("GOT NEW FOR %s WITH args=%s kwargs=%s", cls, args, kwargs)
        return super(zfsBase, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        #logging.debug("GOT INIT FOR %s WITH args=%s kwargs=%s", self, args, kwargs)
        return super(zfsBase, self).__init__(*args, **kwargs)
        #return bases_func(self, '__init__', *args, **kwargs)

#def bases_func(self, name, *args, **kwargs):
#    #for base in self.__class__.__bases__:
#    for base in self.__class__.mro():
#        ret = None
#        func = getattr(base, name, None)
#        if func:
#            ret = func(*args, **kwargs)
#        print "base=%s func=%s ret=%s" % (base, func, ret)





class Property(object):
    name = None
    source = None
    value = None
    parent_name = None

    def __init__(self, **kwargs):
        for k in ['name', 'source', 'value', 'parent_name']:
            setattr(self, k, kwargs.get(k, None))

    def __repr__(self):
        prefix = ''
        source = ''
        if self.source == '-':
            prefix += 'Statistic'
        elif self.source in ['default', 'local']:
            prefix += self.source.capitalize()
        elif self.source:
            prefix += 'Inherited'
            source = ' source=%s' % self.source

        #if self.modified:
        #    prefix += 'Unsaved'

        name = prefix + self.__class__.__name__
        return "%s(%s=%s%s)" % (name, self.name, self.value, source)

    def __unicode__(self):
        return unicode(self.value)

    def __str__(self):
        return str(self.value)

    """
    Property management
    """

    def inherit(self):
        """ Set property to inherit it's value from parent """
        self.__call__(inherit=True)

    def __call__(self, value, inherit=False, modified=True, save=False):
        """ Sets property with value """
        if inherit:
            if self._parent.type == 'pool':
                raise Exception("Cannot save inheritable property %s to %s, not supported by pools" % (self, self._parent))
            else:
                self.inherit = True
                value = None

        self.value = value
        self.modified = modified
        if save:
            self.save()

    def save(self):
        if self.modified:
            if self.inherit:
                return self.parent.inherit(self.name)
            else:
                return self.parent.set(self.name, self.value)
        else:
            return True



class Properties(dict):
    def __init__(self, parent=None):
        self._parent = parent
        self.get()
        # no kwargs since we dont want to start out with data
        return super(Properties, self).__init__()

    #def __getitem__(self, key):
    #    value = self._parent.get(key)
    #
    #    if value:
    #        return self._propify(name=key, value=value)
    #    else:
    #        return KeyError(key)

    def _propify(self, name=None, value=None, source=None):
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)

        if isinstance(value, basestring):
            value = {'value': value}

        if isinstance(value, dict) and 'value' in value:
            value['parent'] = self._parent

            if not 'name' in value and isinstance(name, basestring):
                value['name'] = name
            else:
                raise Exception('Name was not provided')

            value = self._parent._get_type('property')(**value)

        if isinstance(value, Property):
            return value

        else:
            raise Exception('Could not create property object from: %s, %s' % (name, value))

    #def __setitem__(self, key, value):
    #    pass

    #def __delitem__(self, key):
    #    return super(Properties, self).__delitem__(key)

    #def __iter__(self):
    #    return iter([ (x, self.get(x, None)) for x in self.__list__() ])

    #def __list__(self):
    #    return self._parent.get_default_prop_list()

    def get(self, *args, **kwargs):
        for k,v in self._parent.get(*args, **kwargs).iteritems():
            self[k] = v

    #def _save(self):
    #    pass

    # TODO Make this work
    #def reload(self):
    #    if getattr(self, 'name', None):
    #        self.props = self._get_type('properties')(self)


"""
Pool Handling
"""

class PoolBase(object):
    """ Pool base class """
    PROPS = ['name', 'size', 'cap', 'altroot', 'health', 'guid', 'version', 'bootfs', 'delegation', 'replace', 'cachefile', 'failmode', 'listsnaps', 'expand', 'dedupditto',
             'dedup', 'free', 'alloc', 'rdonly', 'ashift']

    @staticmethod
    def zcmd(*args, **kwargs):
        return cmd.zpool(*args, **kwargs)

    #def __init__(self, name, *args, **kwargs):
    #    return super(PoolBase, self).__init__(name, *args, **kwargs)

    def children(self, **kwargs):
        kwargs['skip'] = None
        return self.filesystem.children(**kwargs)

    @property
    def filesystem( self ):
        """ Returns the matching Filesystem for this Pool """
        return self._get_type('filesystem')(name=self.name)

    #@property
    #def filesystem( self ):
    #    """ Returns the matching filesystem for Pool """
    #    return Filesystem.objects.get( pool_id=self.id, name=self.name )

    #def filesystems( self, **kwargs ):
    #    """ Lists filesystems of this pool """
    #    return Filesystem.dbm.objects.filter(name__startswith='%s/'%self.name, **kwargs)

    #def filesystem_create( self, name, **kwargs ):
    #    """ Creates a filesystem in the pool """
    #    logging.info( 'Request to create filesystem (%s) on pool (%s)', name, self.name )
    #    # Get DB entry ready (and validate data)
    #    filesystem = Filesystem( name=name, pool_id=self.id )
    #    filesystem.save()
    #    # Return saved filesystem object
    #    return filesystem

    #def iostat( self, **kwargs ):
    #    """ Returns newly generated ZFS IOStats """
    #    zpool_iostat = zfs.pool.iostat( self.name, **kwargs )
    #    return zpool_iostat[self.name]

    @classmethod
    def iostat(cls, *pools, **kwargs):
        """ Utility to return zpool iostats on the specified pools """
        zargs = ['iostat', '-Tu']
        if pools:
            if not isinstance(pools, list):
                pools = isinstance(pools, basestring) and [pools] or isinstance(pools, tuple) and list(pools)
            zargs.extend(pools)
        capture_length = str(kwargs.get('capture_length', '30'))
        how_many = str(int(kwargs.get('how_many', 1)) + 1)
        zargs.extend([capture_length, how_many])

        iostat = {}
        timestamp = False
        skip_past_dashline = False
        for line in cmd.zpool(*zargs).splitlines():
            line = str(line).rstrip("\n")

            # Got a timestamp
            if line.isdigit():
                # If this is our first record, skip till we get the header seperator
                if not timestamp:
                    skip_past_dashline = True
                # TZify the timestamp
                timestamp = timezone.make_aware(
                    datetime.datetime.fromtimestamp(int(line)), timezone.get_current_timezone() )
                continue

            # If we haven't gotten the dashline yet, wait till the line after it
            if skip_past_dashline == True:
                if line.startswith('-----'):
                    skip_past_dashline = False
                continue

            # If somehow we got here without a timestamp, something is probably wrong.
            if timestamp == False:
                logging.error("Got unexpected input from zpool iostat: %s", line)
                raise Exception

            try:
                # Parse iostats output
                j = {}
                (j['name'], j['alloc'], j['free'], j['iops_read'], j['iops_write'], j['bandwidth_read'],
                 j['bandwidth_write']) = line.split()
                j['timestamp'] = timestamp
                iostat[j['name']] = j
            except:
                logging.error("Could not parse input from zpool iostat: %s", line)
                raise Exception
        return iostat


class Pool(PoolBase, zfsBase):
    """ Pool class """
    pass


class DatasetBase(object):
    """ Dataset class """
    PROPS =  ['name', 'type', 'creation', 'used', 'avail', 'refer', 'ratio', 'mounted', 'origin', 'quota', 'reserv',
              'volsize', 'volblock', 'recsize', 'mountpoint', 'sharenfs', 'checksum', 'compress', 'atime', 'devices',
              'exec', 'setuid', 'rdonly', 'zoned', 'snapdir', 'aclinherit', 'canmount', 'xattr', 'copies', 'version',
              'utf8only', 'normalization', 'case', 'vscan', 'nbmand', 'sharesmb', 'refquota', 'refreserv',
              'primarycache', 'secondarycache', 'usedsnap', 'usedds', 'usedchild', 'usedrefreserv', 'defer_destroy',
              'userrefs', 'logbias', 'dedup', 'mlslabel', 'sync', 'refratio']

    @staticmethod
    def zcmd(*args, **kwargs):
        return cmd.zfs(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        """ Dataset factory; returns back a subclass of dataset as the instance you requested """
        obj_cls = None
        if cls is Dataset or cls is DatasetBase:
        #if True:
            obj_type = kwargs.pop('type', None)
            if not obj_type:
                name = kwargs.get('name')
                if '@' in name:
                    obj_type = 'snapshot'
                else:
                    ## TODO Detect the difference between filesystem/volume
                    obj_type = 'filesystem'
                    #obj_type = 'volume'
            if obj_type:
                obj_cls = cls.ZFS_TYPE_MAP[obj_type]
        return super(DatasetBase, cls).__new__(obj_cls or cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        #logging.debug('GOT INIT AT %s WITH args=%s kwargs=%s', self, args, kwargs)
        return super(DatasetBase, self).__init__(*args, **kwargs)

    @property
    def pool( self ):
        """ Returns the matching Pool for this Dataset """
        return self._get_type('pool')(name=self.path(0, 1))

    def children(self, **kwargs):
        assert hasattr(self, 'name')
        kwargs.update({'depth': kwargs.get('depth', 1),
                       'props': ['name', 'type'],
                       })
        kwargs['self'] = self
        if not 'skip' in kwargs:
            kwargs['skip'] = self.name
        ret = self.list(self.name, **kwargs)
        return ret

    @property
    def parent(self):
        """ Returns the parenta of this Dataset """
        path = self.path()
        if len(path) == 1:
            return None
        return self._get_type('dataset')(name='/'.join(path[:-1]))

    def inherit(self, name, **kwargs):
        zargs = ['inherit']
        # TODO Need module wide cache, tree based so that we can explode cache for all objects in a single line (domino effect, etc)
        #if kwargs.get('recursive') == True: zargs.append('-r')
        zargs += ['%s' % str(name), self.name]
        ret = iterpipes.check_call(cmd.zfs(*zargs))
        self.get(name)
        return ret

    def destroy(self, **kwargs):
        """ [DANGEROUS] Delete dataset from filesystem """
        zargs = ['destroy']
        if kwargs.get( 'recursive', False ) == True: zargs.append('-r')
        if not self.exists(): raise Exception( "Destroy was attempted on a non-existent dataset '%s'" % self.name )
        zargs.append(name)

        logger.info('Destroying %s %s', self.type.capitalize(), name)
        ret = cmd.zfs(*zargs)
        #ret = iterpipes.check_call( cmd.zfs( *zargs ) )
        ret = self.exists() and False or True
        if ret == True:
            self.clear()
            #del(self.props)
            #self.props = self.get()
            self.get()
        return ret

    def create(self, **kwargs):
        """ Create filesystem """
        zargs = ['create']
        # TODO -o opts
        if self.exists(): raise Exception( "Create was attempted on an already existing dataset '%s'" % self.name )
        if not self.name: raise Exception( "Dataset was attempted with an empty name" )
        if '@' in self.name: raise Exception("Create was attempted on a new filesystem with an invalid character '@': '%s'" % name)
        zargs.append(name)

        logging.info('Creating filesystem %s with %s', name, kwargs)
        ret = iterpipes.check_call(cmd.zfs( *zargs ))
        ret = self.exists()
        if ret == True:
            #del(self.props)
            #self.props = self.get()
            self.get()
        return ret

class Dataset(DatasetBase, zfsBase):
    pass

class SnapshottableDatasetBase(object):
    def snapshots(self, **kwargs):
        """ Lists snapshots of this dataset """
        kwargs['type'] = 'snapshot'
        return self.children(**kwargs)

    def filesystems(self, **kwargs):
        kwargs['type'] = 'filesystem'
        return self.children(**kwargs)

    def snapshot(self, name, **kwargs):
        """ Create snapshot """
        zargs = ['snapshot']
        if kwargs.get('recursive', False) == True: zargs.append('-r')
        if not self.name: raise Exception( "Snapshot was attempted with an empty name" )
        #if kwargs.get('name_strftime', True) == True:
        #    name = timezone.now().strftime(name)
        if not self.exists(): raise Exception("Snapshot was attempted on a non-existent dataset '%s'" % self.name)
        name = '%s@%s' % (self.name, name)
        zargs.append(name)

        logging.info('Creating snapshot %s with %s', name, kwargs)
        ret = iterpipes.check_call(cmd.zfs( *zargs ))
        return Snapshot(name)


class FilesystemBase(object):
    """ Filesystem """
    pass

class Filesystem(FilesystemBase, SnapshottableDatasetBase, DatasetBase, zfsBase):
    """ Filesystem """
    pass


class VolumeBase(object):
    """ Volume """
    pass

#class Volume(VolumeBase, SnapshottableDatasetBase, Dataset):
class Volume(VolumeBase, SnapshottableDatasetBase, DatasetBase, zfsBase):
    pass


class SnapshotBase(object):
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

class Snapshot(SnapshotBase, SnapshottableDatasetBase, Dataset):
    pass


ZFS_TYPE_MAP.update({
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    'properties': Properties,
})
