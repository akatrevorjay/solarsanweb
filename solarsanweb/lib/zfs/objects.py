""""
$ zfs/class_hell.py -- Interface to zfs command line utilities (class based)
~ Trevor Joynson (aka trevorj) <trevorj@localhostsolutions.com>
"""

import os, sys
import time, datetime, logging
from django.utils import timezone
#from iterpipes import run, cmd, linecmd, check_call, format
import iterpipes
from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
from django.core.cache import cache
from .common import Error, NotImplemented
import pool, dataset, cmd, common

#from mongoengine.fields import *
#from mongoengine import *
#import mongoengine


ZFS_PROPS = {
    'Pool':     ['name', 'size', 'cap', 'altroot', 'health', 'guid', 'version', 'bootfs', 'delegation', 'replace', 'cachefile', 'failmode', 'listsnaps', 'expand', 'dedupditto',
                 'dedup', 'free', 'alloc', 'rdonly', 'ashift'],
    'Dataset':  ['name', 'type', 'creation', 'used', 'avail', 'refer', 'ratio', 'mounted', 'origin', 'quota', 'reserv', 'volsize', 'volblock', 'recsize', 'mountpoint',
                 'sharenfs', 'checksum', 'compress', 'atime', 'devices', 'exec', 'setuid', 'rdonly', 'zoned', 'snapdir', 'aclinherit', 'canmount', 'xattr', 'copies', 'version',
                 'utf8only', 'normalization', 'case', 'vscan', 'nbmand', 'sharesmb', 'refquota', 'refreserv', 'primarycache', 'secondarycache', 'usedsnap', 'usedds', 'usedchild',
                 'usedrefreserv', 'defer_destroy', 'userrefs', 'logbias', 'dedup', 'mlslabel', 'sync', 'refratio'],
    }

class CachedDataTree(dict):
    prefix = 'zfs_obj_tree'
    #def __len__(self):
    #    return len(self.values)
    def __getitem__(self, key):
        print 'get key=%s' % key
        #if 'values' not in self.__dict__: self.values = {}
        #if not key in self.values or self.values[key]['ts'] < datetime.datetime.now():
        #    self.values[key] = {'ts': datetime.datetime.now(),
        #                        'obj': cache.get('%s__%s' % (self.prefix, key)),
        #                        }
        #return self.values[key]['obj']
        return cache.get('%s__%s' % (self.prefix, key))
    def __setitem__(self, key, value):
        print 'set key=%s value=%s' % (key, value)
        cache.set('%s__%s' % (self.prefix, key), value, 15)
        #self.values[key] = value
    #def __delitem__(self, key):
    #    del self.values[key]
    #def __iter__(self):
    #    return iter(self.values)
    #def __reversed__(self):
    #    return reversed(self.values)

OBJ_TREE = {}
#OBJ_TREE = CachedDataTree()

"""
Base
"""

class zfsBase(object):
    """ Base class """
    meta = {'collection': 'storage_base',
            'allow_inheritance': True,
            'indexes': [{'fields': ['name'], 'unique': True}],
            }
    #abstract = True
    #props = ListField(EmbeddedDocumentField(Property))
    _zfs_type = 'base'
    def __new__(cls, name, *args, **kwargs):
        if name in OBJ_TREE and cls.__name__ in OBJ_TREE[name]:
            return OBJ_TREE[name][cls.__name__]
        self = super(zfsBase, cls).__new__(cls, *args, **kwargs)

        if not name in OBJ_TREE: OBJ_TREE[name] = {}
        OBJ_TREE[name][self.__class__.__name__] = self

        return self

    def __init__(self, *args, **kwargs):
        """ Initialize """
        #print '__init__ args=%s kwargs=%s' % (args, kwargs)
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

        if not getattr(self, 'props', False):
            self.props = Properties(self, lazy=kwargs.get('lazy', False))

        #self.clear()

    def __repr__(self):
        name = getattr(self, 'name', None)
        return "%s('%s')" % (type(self).__name__, name)

    #idumps  = lambda self: `self`
    #__str__ = lambda self: self.dumps()

    def path( self, start=0, len=None ):
        """ Splits name of object into paths starting at index start """
        return self.name.split( '/' )[start:len]

    #@property
    def exists(self):
        #if 'type' in getattr(self, 'props', {}):
        if 'type' in self.props:
            return True
        return False

    @property
    def type(self):
        return self.parent.__class__.__name__

    @classmethod
    def get_prop_list(cls):
        for subclass in zfsBase.__subclasses__():
            if issubclass(cls, subclass) or subclass == cls:
                return ZFS_PROPS[subclass.__name__]

    #def get(self, *args, **kwargs):
    def get(self, *args, **kwargs):
        kwargs['walk_only'] = [self.name]
        #print 'get args=%s kwargs=%s' % (args, kwargs)
        return self._get(*args, **kwargs)

    @classmethod
    def _get(cls, *args, **kwargs):
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
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])

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
            (obj_name, name, value, source) = [line[cols[x]: x+1 == len(cols) and len(line) or cols[x+1] ].strip() for x in xrange(len(cols))]
            #print 'obj_name=%s name=%s value=%s source=%s' % (obj_name, name, value, source)
            if not obj_name:
                continue

            # As far as I know, this is always returned first (on Datasets, not returned at all for pool), but we may not want to rely on this.
            if obj_name != last_obj_name:
                #print 'new obj_name from last_obj_name! %s %s' % (obj_name, last_obj_name)

                #obj_cls = None
                #if name == 'type':
                #    for subclass in Dataset.__subclasses__():
                #        if value == subclass.__name__.lower():
                #            obj_cls = subclass
                #            break
                #if not obj_cls and cls == Pool: obj_cls = Pool
                #if not obj_name in objs: objs[obj_name] = {}
                ##print 'obj_cls=%s' % obj_cls
                #if not obj_cls.__name__ in objs[obj_name]: objs[obj_name][obj_cls.__name__] = obj_cls(obj_name)
                #o = objs[obj_name][obj_cls.__name__]

                if not obj_name in ret: ret[obj_name] = {}
            ret[ obj_name ][ name ] = {'value': value, 'source': source}

            last_obj_name = obj_name

        # If we're a dataset and recursive opt is set, return the full hash including dataset name as first key
        if Dataset.__subclasscheck__(cls) and kwargs.get('recursive'): return ret

        # If we only requested a single property from a single object that isn't the magic word 'all', just return the value.
        if not kwargs.get('recursive') and len(args) == 1 and 'all' not in args: ret = ret[ret.keys()[0]]
        return ret[ret.keys()[0]]

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


class Property(object):
    def __init__(self, **kwargs):
        #kwargs.setdefault('modified', False)
        #kwargs.setdefault('inherit', False)
        self.modified = False
        self.inherit = False
        self.source = 'local'
        self.lazy = False
        self.value = None

        for k in ['name', 'source', 'value', 'parent', 'inherit', 'modified', 'lazy']:
            if k in kwargs:
                setattr(self, k, kwargs.get(k))

        if self.lazy and not self.value:
            self.value = self._lazy_value

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        prefix = ''
        source = getattr(self, 'source')
        vars = {}

        if self.lazy and not self.modified:
            prefix += 'Lazy'

        else:
            if source in ['default', 'local']:
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

    @property
    def _lazy_value(self):
        return self.parent.get(self.name)

class Properties(dict):
    def __init__(self, parent=None, lazy=False, cache=True):
        self._parent = parent
        self.lazy = lazy
        self.cache = cache

        # no kwargs since we dont want to start out with data
        super(Properties, self).__init__()

        #if not self.lazy and self.cache:
        #    self.refresh()
        #else:
        #    for p in self._parent.get_prop_list():
        #        self[p] = Property(name=p, parent=self._parent, lazy=True)

    def __getitem__(self, key, refresh=False):
        cache = self.cache

        if not cache:
            refresh = True

        if refresh or key not in self:
            ## TODO Timestamp caching?
            if cache and getattr(self, '_refresh_ts', None) == None:
                self.refresh()
                value = self[key]
            else:
                value = self._parent.get(key)

                if isinstance(value, dict):
                    value = self._propify(name=key, value=value)

                if cache:
                    self[ key ] = value

            return value
        else:
            if cache:
                value = super(Properties, self).__getitem__(key)

        return value

    def _propify(self, name=None, value=None):
            if isinstance(value, int) or isinstance(value, float):
                value = str(value)

            if isinstance(value, basestring):
                value = {'value': value}

            if isinstance(value, dict) and 'value' in value:
                value['parent'] = self._parent

                if 'name' in value and isinstance(name, basestring):
                    value['name'] = name
                else:
                    raise Exception('Name was not provided')

                value = Property(**value)

            if isinstance(value, Property):
                return value

            else:
                raise Exception('Could not create property object from: %s, %s' % (name, value))

    def __setitem__(self, key, value):
        if self.cache:
            if key in self:
                if isinstance(value, dict):
                    value = value['value']
                if value != self[ key ].value:
                    self[ key ](value)
            else:
                value = self._propify(name=key, value=value)
                return super(Properties, self).__setitem__(key, value)

    #def __delitem__(self, key):
    #    return super(Properties, self).__delitem__(key)

    #def __iter__(self):
    #    return iter(self.__list__())

    def __list__(self):
        return self._parent.get_prop_list()

    def get(self, *args, **kwargs):
        for k,v in self._parent.get(*args, **kwargs).iteritems():
            v['name'] = k
            self[k] = v
    refresh = get

    #def _save(self):
    #    pass


"""
Pool Handling
"""

class Pool( zfsBase ):
    """ Pool class """
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



class Dataset( zfsBase ):
    """ Dataset class """
    _zfs_type = 'dataset'

    #def __init__(self, name, *args, **kwargs):
    #    super(Dataset, self).__init__(name, *args, **kwargs)

    def __new__(cls, *args, **kwargs):
        if 'type' in kwargs:
            for subclass in Dataset.__subclasses__():
                #if subclass._zfs_type == kwargs['type']:
                #    return super(Dataset, cls).__new__(subclass, *args, **kwargs)
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
        """ Returns the matching Pool for this Filesystem """
        return Pool(self.path(0, 1))

    @property
    def parent(self):
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



ZFS_TYPE_MAP = {
    'pool': Pool,
    'dataset': Dataset,
    'filesystem': Filesystem,
    'volume': Volume,
    'snapshot': Snapshot,
    }


