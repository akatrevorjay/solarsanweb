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

from .common import Error, NotImplemented
import pool, dataset, cmd, common



ZFS_PROPS = {
    'Pool':     ['name', 'size', 'cap', 'altroot', 'health', 'guid', 'version', 'bootfs', 'delegation', 'replace', 'cachefile', 'failmode', 'listsnaps', 'expand', 'dedupditto',
                 'dedup', 'free', 'alloc', 'rdonly', 'ashift'],
    'Dataset':  ['name', 'type', 'creation', 'used', 'avail', 'refer', 'ratio', 'mounted', 'origin', 'quota', 'reserv', 'volsize', 'volblock', 'recsize', 'mountpoint',
                 'sharenfs', 'checksum', 'compress', 'atime', 'devices', 'exec', 'setuid', 'rdonly', 'zoned', 'snapdir', 'aclinherit', 'canmount', 'xattr', 'copies', 'version',
                 'utf8only', 'normalization', 'case', 'vscan', 'nbmand', 'sharesmb', 'refquota', 'refreserv', 'primarycache', 'secondarycache', 'usedsnap', 'usedds', 'usedchild',
                 'usedrefreserv', 'defer_destroy', 'userrefs', 'logbias', 'dedup', 'mlslabel', 'sync', 'refratio'],
    }


DATA_TREE = {}
OBJ_TREE = DATA_TREE['objs'] = {
                            }

"""
Base
"""

class zfsBase( object ):
    """ Base class """
    _zfs_type = 'base'

    def __new__(cls, name, *args, **kwargs):
        if name in OBJ_TREE and cls.__name__ in OBJ_TREE[name]:
            return OBJ_TREE[name][cls.__name__]
        self = super(zfsBase, cls).__new__(cls, *args, **kwargs)

        if not name in OBJ_TREE: OBJ_TREE[name] = {}
        OBJ_TREE[name][self.__class__.__name__] = self

        return self

    def __init__(self, name, *args, **kwargs):
        """ Initialize """
        #print '__init__ args=%s kwargs=%s' % (args, kwargs)
        self.name = name
        if not getattr(self, 'props', False):
            self.props = {}
            self.get()
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
        if 'type' in getattr(self, 'props', {}):
            return True
        return False

    @property
    def type(self):
        return self.parent.__class__.__name__

    #def get(self, *args, **kwargs):
    def get(self, *args, **kwargs):
        kwargs['walk_only'] = [self.name]
        print 'get args=%s kwargs=%s' % (args, kwargs)
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

        # The zfs command has gotten a few interface tweaks over the years that give it en edge over zpool
        if cls == Dataset or Dataset.__subclasscheck__(cls):
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])

        zargs += [','.join(args).lower(), ]
        zargs.extend(walk_only)

        if cls == Dataset or Dataset.__subclasscheck__(cls):
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

            # As far as I know, this is always returned first (on Datasets, not returned at all for pool), but we may not want to rely on this.
            if obj_name != last_obj_name:
                #print 'new obj_name from last_obj_name! %s %s' % (obj_name, last_obj_name)

                obj_cls = None
                if name == 'type':
                    if value == 'filesystem':
                        obj_cls = Filesystem
                    elif value == 'snapshot':
                        obj_cls = Snapshot
                    elif value == 'volume':
                        obj_cls = Volume
                    #elif value == 'dataset':
                    #    obj_cls = Dataset
                if not obj_cls and cls == Pool:
                    obj_cls = Pool
                #    if cls == Dataset or Dataset.__subclasscheck__(cls):
                #        obj_cls = Dataset
                #    elif cls == Pool or Pool.__subclasscheck__(cls):
                #        obj_cls = Pool
                if not obj_name in objs: objs[obj_name] = {}
                #if not obj_cls: raise Exception('Could not figure out what class an object is supposed to be')
                print 'obj_cls=%s' % obj_cls
                if not obj_cls.__name__ in objs[obj_name]: objs[obj_name][obj_cls.__name__] = obj_cls(obj_name)
                o = objs[obj_name][obj_cls.__name__]

                if obj_name in walk_only: ret[obj_name] = o

            o.props[ name ] = Property(name=name, value=value, source=source, obj=o)
            if value == '-' and source == '-' and name in o.props: del(o.props[name])

            last_obj_name = obj_name
        # If we're a dataset and recursive opt is set, return the ful hash including dataset name as first key
        if cls == Dataset or Dataset.__subclasscheck__(cls) and kwargs.get('recursive'): return ret

        if len(args) == 1 and 'all' not in args: ret = ret[ret.keys()[0]]
        return ret[ret.keys()[0]]

    def set(self, name, value, **kwargs):
        zargs = ['set', '%s=%s' % (str(name), str(value)), self.name]
        print 'set name=%s value=%s xargs=%s' % (name, value, zargs)
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
        zargs += ['-o', ','.join(props).lower(), ]

        # ZFS object selection (pool/dataset starting point for walking tree, etc)
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        zargs.extend(args)

        # Datasets (the zfs command in particular) have a better CLI interface, so allow for more control when it comes to those
        if cls == Dataset or Dataset.__subclasscheck__(cls):
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'type' in kwargs: zargs += ['-t', kwargs.get('type')]
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])

        # Prep vars, trying out an idea by keeping all objects per active dataset/pool referenced to here, that way they are all in sync (hopefully?)
        objs = OBJ_TREE
        ret = {}

        # Generate command and execute, parse output
        if cls == Dataset or Dataset.__subclasscheck__(cls):
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

            # Inject the props we can get from the list into the object
            # (is this even needed at all or would it be better to just use get for this sort of thing since it gets ALL props in one go?)
            #objs[parent_name].props.update( dict([(k, Property(name=k, value=v, parent=objs[parent_name])) for k,v in line.iteritems() ]) )

            if cls == Dataset or Dataset.__subclasscheck__(cls):
                if '@' in parent_name: obj_cls = Snapshot
                else: obj_cls = Filesystem
            else:
                obj_cls = Pool

            ret[ parent_name ] = objs[parent_name][obj_cls.__name__]
        return ret


class Property(object):
    def __init__(self, **kwargs):
        for k in ['name', 'source', 'value', 'parent']:
            #setattr(self, k, unicode(kwargs.get(k)))
            setattr(self, k, kwargs.get(k))
    def __str__(self):
        return str(self.value)
    def __unicode__(self):
        return unicode(self.value)
    def __repr__(self):
        return "Property('%s', source='%s')" % (self.value, self.source)
    def __setattr__(self, name, value):
        """ This is  here to automatically save property values """
        if hasattr(self, 'parent') and name == 'value': self.parent.set(self.name, value)
        #if name == 'value' and hasattr(self, 'parent'): return self.parent.set(self.parent, name, value)
        return super(Property, self).__setattr__(name, value)


#class Properties(object):
#    def __init__(self, parent):
#        self.parent = parent
#    def __getattribute__(self, attr):
#        if attr == 'parent':
#            return super(Properties, self).__getattribute__(attr)
#        elif attr in self.parent._props:
#            return self.parent._get_prop(attr)
#        elif attr == 'all':
#            return self.parent._get_prop(*self.parent._props)
#        else:
#            return super(Properties, self).__getattribute__(attr)
#    def __call__(self, prop=None):
#        if prop:
#            return self.parent._get_prop(prop)
#        return self.parent._props



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
        elif '@' in args[0]:
            cls = Snapshot
        else:
            cls = Filesystem
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












