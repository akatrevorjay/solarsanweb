""""
$ zfs/class_hell.py -- Interface to zfs command line utilities (class based)
~ Trevor Joynson (aka trevorj) <trevorj@localhostsolutions.com>
"""

import os
import sys
import time
import datetime
import logging
import iterpipes

import cmd
import common
import dataset
import models as z

from .common import Error, NotImplemented
from django.utils import timezone
from solarsan.utils import FilterableDict, CacheDict, convert_bytes_to_human, convert_human_to_bytes


ZFS_PROPS = {
    'Pool':     ['name', 'size', 'cap', 'altroot', 'health', 'guid', 'version', 'bootfs', 'delegation', 'replace', 'cachefile', 'failmode', 'listsnaps', 'expand', 'dedupditto',
                 'dedup', 'free', 'alloc', 'rdonly', 'ashift'],
    'Dataset':  ['name', 'type', 'creation', 'used', 'avail', 'refer', 'ratio', 'mounted', 'origin', 'quota', 'reserv', 'volsize', 'volblock', 'recsize', 'mountpoint',
                 'sharenfs', 'checksum', 'compress', 'atime', 'devices', 'exec', 'setuid', 'rdonly', 'zoned', 'snapdir', 'aclinherit', 'canmount', 'xattr', 'copies', 'version',
                 'utf8only', 'normalization', 'case', 'vscan', 'nbmand', 'sharesmb', 'refquota', 'refreserv', 'primarycache', 'secondarycache', 'usedsnap', 'usedds', 'usedchild',
                 'usedrefreserv', 'defer_destroy', 'userrefs', 'logbias', 'dedup', 'mlslabel', 'sync', 'refratio'],
    }


#OBJ_TREE = CacheDict()
OBJ_TREE = {}


"""
Base
"""

class zfsBase(object):
    """ Base class """

    dbm = z.zfsBaseDocument
    _zfs_type = 'base'

    flags = {
            'obj_tree': False,
            'db': True,
            }

    """
    Magic
    """

    def __new__(cls, name, *args, **kwargs):
        obj_tree = kwargs.get('obj_tree', cls.flags.get('obj_tree'))
        if obj_tree:
            if name in OBJ_TREE and cls.__name__ in OBJ_TREE[name]:
                return OBJ_TREE[name][cls.__name__]

        self = super(zfsBase, cls).__new__(cls, *args, **kwargs)

        if obj_tree:
            if not name in OBJ_TREE:
                OBJ_TREE[name] = {}
            OBJ_TREE[name][self.__class__.__name__] = self

        return self

    def __init__(self, *args, **kwargs):
        """ Initialize """
        # Name
        name = kwargs.get('name', args[0])
        if 'name' in kwargs:
            name = kwargs.pop('name')
        else:
            if not isinstance(args, list):
                args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
            if not len(args[0]) > 0:
                raise Exception('No name was given')
            name = kwargs['name'] = args.pop(0)

        self.name = name

        # If db is turned off for this object, disable db
        if not kwargs.get('db', True):
            self.flags.update(db=False)

        # Props
        if not getattr(self, 'props', None):
            self.props = Properties(self)

    def __repr__(self):
        name = getattr(self, 'name', None)
        return "%s('%s')" % (type(self).__name__, name)

    #idumps  = lambda self: `self`
    #__str__ = lambda self: self.dumps()


    """
    Mongo Glue
    """

    @property
    def dbo(self):
        """ Returns database object """

        if not self.flags.get('db'):
            raise AttributeError("DB support is disabled for this instance '%s'" % self)

        if not getattr(self, '_dbo', None):
            lookup_data = {'name': self.name,
                           'auto_save': False}
            self._dbo, created = self.dbm.objects.get_or_create(name=self.name,
                                                                auto_save=False)
            if created:
                # New in DB, fill with zfs values
                logging.warning("Creating dbo for %s '%s'", self.type, self.name)
                dbo = self._dbo

        return self._dbo

    @property
    def id(self):
        return self.dbo.id

    def save(self, *args, **kwargs):
        return self.dbo.save(*args, **kwargs)



    """
    Instance
    """

    def path( self, start=0, len=None ):
        """ Splits name of object into paths starting at index start """
        return self.name.split( '/' )[start:len]

    def exists(self, force_check=False):
        """ Checks if object exists """
        # If we're not forced, just see if this entry's already in the db. If it's not, then do a check anyway.
        if not force_check and self.flags.get('db'):
            if getattr(self, 'dbo', None):
                return True

        # Check if type property is there, should always be there.
        try:
            self.list(self.name)
            if 'type' in self.props:
                return True
        except:
            return False

    @property
    def type(self):
        """ Returns ZFS object type string """
        return self._zfs_type

    @classmethod
    def get_prop_list(cls):
        """ Returns list of default property names """
        return ZFS_PROPS[self._zfs_type]

    def get(self, *args, **kwargs):
        """ Returns requested properties *args with **kwargs opts for self """
        kwargs['walk_only'] = [self.name]
        return self._get(*args, **kwargs)

    def set(self, name, value, **kwargs):
        zargs = ['set', '%s=%s' % (str(name), str(value)), self.name]
        #print 'set name=%s value=%s xargs=%s' % (name, value, zargs)
        zcmd = isinstance(self, Dataset) and cmd.zfs(*zargs) or cmd.zpool(*zargs)
        ret = iterpipes.check_call(zcmd)
        self.get(name)
        return ret

    def clear(self):
        self.props = {}
        self.get()

    """
    Class
    """

    @classmethod
    def list(cls, *args, **kwargs):
        zargs = ['list', '-H']

        # Property selection
        props = kwargs.get('props', ['name'])
        if not isinstance(props, list):
            props = isinstance(props, basestring) and [props] or isinstance(props, tuple) and list(props)
        if Dataset.__subclasscheck__(cls) and 'type' not in props: props += ['type']
        zargs += ['-o', ','.join(props).lower(), ]

        # ZFS object selection (pool/dataset starting point for walking tree, etc)
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        zargs.extend(args)

        # Datasets (the zfs command in particular) have a better CLI interface, so allow for more control when it comes to those
        if Dataset.__subclasscheck__(cls):
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'type' in kwargs: zargs += ['-t', kwargs.get('type')]
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])

        # Prep vars, trying out an idea by keeping all objects per active dataset/pool referenced to here, that way they are all in sync (hopefully?)
        objs = OBJ_TREE
        ret = {}

        # Generate command and execute, parse output
        if Dataset.__subclasscheck__(cls):
            zcmd = cmd.zfs(*zargs)
        else:
            zcmd = cmd.zpool(*zargs)

        for line in iterpipes.run(zcmd):
            line = dict(zip(props == ['all'] and ZFS_PROPS[cls.__name__] or props,
                            str(line).rstrip("\n").split()))
            parent_name = line['name']
            if not parent_name in objs: objs[parent_name] = {}
            if cls.__name__ not in objs[parent_name]:
                o = cls(parent_name)
                objs[parent_name][o.__class__.__name__] = o

            obj_cls = None
            obj_type = line.get('type', 'pool')
            if obj_type == 'filesystem':
                obj_cls = Filesystem
            elif obj_type == 'snapshot':
                obj_cls = Snapshot
            elif obj_type == 'volume':
                obj_cls = Volume
            elif obj_type == 'pool':
                obj_cls = Pool

            o = objs[parent_name][obj_cls.__name__]
            ret[ parent_name ] = o
        return ret


    @classmethod
    def _get(cls, *args, **kwargs):
        """ Returns requested properties *args with **kwargs opts """
        zargs = ['get']

        # Props
        args = args or ['all']
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)

        # Object[s] to start walking tree from
        walk_only = kwargs.get('walk_only', [])
        if not isinstance(walk_only, list):
            walk_only = isinstance(walk_only, basestring) and [walk_only] or isinstance(walk_only, tuple) and list(walk_only)
        if not walk_only and cls == Pool: raise Exception('Cannot _get Pools without giving me a list (walk_only)')

        # The zfs command has gotten a few interface tweaks over the years that give it en edge over zpool
        if Dataset.__subclasscheck__(cls):
            if kwargs.get('recursive'):
                zargs.append('-r')
            if 'source' in kwargs:
                zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs:
                zargs.extend(['-d', int(kwargs['depth'])])

        # Build prop list to grab
        zargs += [','.join(args).lower(), ]
        if walk_only: zargs.extend(walk_only)

        if Dataset.__subclasscheck__(cls):
            zcmd = cmd.zfs(*zargs)
        else:
            zcmd = cmd.zpool(*zargs)

        # Prep vars, trying out an idea by keeping all objects per active dataset/pool referenced to here, that way they are all in sync (hopefully?)
        objs = OBJ_TREE
        ret = {}
        skip = 1
        last_obj_name = ''
        for line in iterpipes.run(zcmd):
            line = str(line).rstrip("\n")
            if skip > 0:
                skip -= 1
                cols = [ line.index(col) for col in line.split() ]
                continue
            #(obj_name, name, value, source) = [line[cols[x]: x+1 == len(cols) and len(line) or cols[x+1] ].strip() for x in xrange(len(cols))]
            (obj_name, name, value, source) = line.split(None, len(cols))
            #print 'obj_name=%s name=%s value=%s source=%s' % (obj_name, name, value, source)
            if not obj_name:
                continue

            # As far as I know, this is always returned first (on Datasets, not returned at all for pool), but we may not want to rely on this.
            if obj_name != last_obj_name:
                if not obj_name in ret: ret[obj_name] = {}
            ret[ obj_name ][ name ] = {'value': value, 'source': source}

            last_obj_name = obj_name

        # If we're a dataset and recursive opt is set, return the full hash including dataset name as first key
        if Dataset.__subclasscheck__(cls) and kwargs.get('recursive'): return ret

        # If we only requested a single property from a single object that isn't the magic word 'all', just return the value.
        if not kwargs.get('recursive') and len(args) == 1 and 'all' not in args: ret = ret[ret.keys()[0]]
        return ret[ret.keys()[0]]



class Property(object):
    def __init__(self, **kwargs):
        #kwargs.setdefault('modified', False)
        #kwargs.setdefault('inherit', False)
        self.modified = False
        self.inherit = False
        self.source = 'local'
        self.value = None

        for k in ['name', 'source', 'value', 'parent', 'inherit', 'modified']:
            if k in kwargs:
                setattr(self, k, kwargs.get(k))

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        prefix = ''
        source = getattr(self, 'source')
        vars = {}

        if source == '-':
            prefix += 'Statistic'

        elif source in ['default', 'local']:
            prefix += self.source.capitalize()

        elif source:
            prefix += 'Inherited'
            vars['source'] = source

        if self.modified:
            prefix += 'Unsaved'

        vars['value'] = self.value

        name = prefix + self.__class__.__name__
        return "%s(**%s)" % (name, vars)

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

    def has_parent(self):
        return getattr(self, 'parent', None) != None

    #@property
    #def _lazy_value(self):
    #    return self.parent.get(self.name)


class Properties(dict):
    def __init__(self, parent=None):
        self._parent = parent

        # no kwargs since we dont want to start out with data
        super(Properties, self).__init__()

    def __getitem__(self, key):
        value = self._parent.get(key)

        if value:
            return self._propify(name=key, value=value)
        else:
            return KeyError(k)

    def _propify(self, name=None, value=None):
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

                value = Property(**value)

            if isinstance(value, Property):
                return value

            else:
                raise Exception('Could not create property object from: %s, %s' % (name, value))

    def __setitem__(self, key, value):
        pass

    #def __delitem__(self, key):
    #    return super(Properties, self).__delitem__(key)

    def __iter__(self):
        return iter([ (x, self.get(x, None)) for x in self.__list__() ])

    def __list__(self):
        return self._parent.get_prop_list()

    def get(self, *args, **kwargs):
        for k,v in self._parent.get(*args, **kwargs).iteritems():
            v['name'] = k
            self[k] = v

    #def _save(self):
    #    pass


"""
Pool Handling
"""

class Pool( zfsBase ):
    """ Pool class """
    dbm = z.PoolDocument
    _zfs_type = 'pool'

    #def __init__(self, name, *args, **kwargs):
    #    super(Pool, self).__init__(name, *args, **kwargs)

    @property
    def filesystem( self ):
        """ Returns the matching Filesystem for this Pool """
        return Filesystem(self.name)

    def iostat(*pools, **kwargs):
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
        for line in iterpipes.run(cmd.zpool(*zargs)):
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
                raise Error

            try:
                # Parse iostats output
                j = {}
                (j['name'], j['alloc'], j['free'], j['iops_read'], j['iops_write'], j['bandwidth_read'],
                 j['bandwidth_write']) = line.split()
                j['timestamp'] = timestamp
                iostat[j['name']] = j
            except:
                logging.error("Could not parse input from zpool iostat: %s", line)
                raise Error
        return iostat

    def cached_status(self):
        """ Snags pool status and vdev info from zdb as zpool status kind of sucks """
        z = cmd.ZdbCommand('-C', '-v')
        ret = z(ofilter=cmd.SafeYamlFilter)
        self._parse_vdev_info(ret)
        return ret

    def _parse_vdev_info(self, ret):
        ## TODO Take some of this wonderous info and put it to good use besides just returning it. ##

        for pool in ret.keys():
            if not pool == self.name:
                continue # temporary

            # Basic info
            self.pool_guid = ret[pool]['pool_guid']
            self.state = ret[pool]['state']
            self.txg = ret[pool]['txg']
            self.version = ret[pool]['version']

            # Snag vdevs
            self.vdev_children = ret[pool]['vdev_children']
            self.vdev_tree = ret[pool]['vdev_tree']

        #return ret




class Dataset( zfsBase ):
    """ Dataset class """
    dbm = z.DatasetDocument
    _zfs_type = 'dataset'

    #def __init__(self, name, *args, **kwargs):
    #    super(Dataset, self).__init__(name, *args, **kwargs)

    def __new__(cls, *args, **kwargs):
        """ Dataset factory; returns back a subclass of dataset as the instance you requested """
        if 'type' in kwargs:
            for subclass in Dataset.__subclasses__():
                if kwargs['type'] in ZFS_TYPE_MAP:
                    return super(Dataset, cls).__new__(ZFS_TYPE_MAP[ kwargs['type'] ], *args, **kwargs)
            raise Exception, 'Dataset type not supported'
        elif '@' in args[0]:
            cls = ZFS_TYPE_MAP['snapshot']
        else:
            cls = ZFS_TYPE_MAP['filesystem']
        return super(Dataset, cls).__new__(cls, *args, **kwargs)

    @property
    def pool( self ):
        """ Returns the matching Pool for this Dataset """
        return Pool(self.path(0, 1))

    @property
    def parent(self):
        """ Returns the parenta of this Dataset """
        path = self.path()
        if len(path) == 1:
            return None
        return Dataset('/'.join(path[:-1]))

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
        return [(Dataset(x, type=y['type'])) for x,y in dataset.list(self.name, type=kwargs.get('type', 'all'), prop=['name', 'type'], depth=kwargs.get('depth', 1)).iteritems() if y['name'] != self.name]

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



class Filesystem( Dataset, SnapshottableDataset ):
    dbm = z.FilesystemDocument
    _zfs_type = 'filesystem'
    """ Filesystem """
    pass


class Volume( Dataset, SnapshottableDataset ):
    dbm = z.VolumeDocument
    _zfs_type = 'volume'
    """ Volume """
    pass


class Snapshot( Dataset ):
    dbm = z.SnapshotDocument
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



ZFS_TYPE_MAP = {
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    }
