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


DATA_TREE = {}

"""
Base
"""

class zfsBase( object ):
    """ Base class """
    _zfs_type = 'base'

    #def __new__(cls, *args, **kwargs):
    #    return super(zfsBase, cls).__new__(cls, *args, **kwargs)

    def __init__(self, name, *args, **kwargs):
        """ Initialize """
        self.name = name
        self.clear()

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

    def get(self, *args, **kwargs):
        args = args or ['all']
        zargs = ['get']
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)

        if isinstance(self, Dataset):
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])

        zargs += [','.join(args).lower(), self.name]
        zcmd = isinstance(self, Dataset) and cmd.zfs(*zargs) or cmd.zpool(*zargs)

        parents = {}
        ret = {}
        skip = 1
        for line in iterpipes.run(zcmd):
            line = str(line).rstrip("\n")
            if skip > 0:
                skip -= 1
                cols = [ line.index(col) for col in line.split() ]
                continue
            (parent_name, name, value, source) = [line[cols[x]: x+1 == len(cols) and len(line) or cols[x+1] ].strip() for x in xrange(len(cols))]
            if not parent_name in ret:
                parents[parent_name] = parent_name == self.name and self or isinstance(self, Dataset) and Dataset(parent_name)
                ret[parent_name] = {}
            ret[ parent_name ][ name ] = Property(name=name, value=value, source=source, parent=parents[parent_name])
            if parent_name == self.name:
                if value == '-' and source == '-' and name in self.props: del(self.props[name])
                else: self.props[name] = ret[parent_name][name]

        # If we're a dataset and recursive opt is set, return the ful hash including dataset name as first key
        if isinstance(self, Dataset) and kwargs.get('recursive'): return ret
        # Otherwise, return the first (and should be only) result
        if len(args) == 1 and 'all' not in args: ret = ret[ret.keys()[0]]
        return ret[ret.keys()[0]]

    def set(self, name, value, **kwargs):
        zargs = ['set', '%s=%s' % (str(name), str(value)), self.name]
        #print 'name=%s value=%s xargs=%s' % (name, value, zargs)
        zcmd = isinstance(self, Dataset) and cmd.zfs(*zargs) or cmd.zpool(*zargs)
        ret = iterpipes.check_call(zcmd)
        self.get(name)
        return ret

    def clear(self):
        self.props = {}
        self.get()


    @classmethod
    def list(cls, *args, **kwargs):
        props = kwargs.get('props', ['all'])
        if not isinstance(props, list):
            props = isinstance(props, basestring) and [props] or isinstance(props, tuple) and list(props)
        zargs = [ 'list', '-H', '-o', ','.join(props).lower(), ]
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        zargs.extend(args)

        if isinstance(cls, Dataset) or cls == Dataset:
            if props == ['all']: col_names = ['name', 'type', 'creation', 'used', 'avail', 'refer', 'ratio', 'mounted', 'origin', 'quota', 'reserv', 'volsize', 'volblock', 'recsize', 'mountpoint', 'sharenfs', 'checksum', 'compress', 'atime', 'devices', 'exec', 'setuid', 'rdonly', 'zoned', 'snapdir', 'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only', 'normalization', 'case', 'vscan', 'nbmand', 'sharesmb', 'refquota', 'refreserv', 'primarycache', 'secondarycache', 'usedsnap', 'usedds', 'usedchild', 'usedrefreserv', 'defer_destroy', 'userrefs', 'logbias', 'dedup', 'mlslabel', 'sync', 'refratio']
            if kwargs.get('recursive') == True: zargs.append('-r')
            if 'type' in kwargs: zargs += ['-t', kwargs.get('type')]
            if 'source' in kwargs: zargs.extend(['-s', str(kwargs['source'])])
            if 'depth' in kwargs: zargs.extend(['-d', int(kwargs['depth'])])
        else:
            if props == ['all']: col_names = ['name', 'size', 'cap', 'altroot', 'health', 'guid', 'version', 'bootfs', 'delegation', 'replace', 'cachefile', 'failmode', 'listsnaps', 'expand', 'dedupditto', 'dedup', 'free', 'alloc', 'rdonly', 'ashift']

        if 'objs' not in DATA_TREE: DATA_TREE['objs'] = {}
        if cls.__name__ not in DATA_TREE['objs']: DATA_TREE['objs'][cls.__name__] = {}
        objs = DATA_TREE['objs'][cls.__name__]
        ret = {}

        zcmd = isinstance(cls, Dataset) or cls == Dataset and cmd.zfs(*zargs) or cmd.zpool(*zargs)
        for line in iterpipes.run(zcmd):
            line = dict(zip(col_names, str(line).rstrip("\n").split()))
            parent_name = line['name']
            if not parent_name in objs:
                objs[parent_name] = cls(parent_name)
            # Inject the props we can get from the list into the object
            # (is this even needed at all or would it be better to just use get for this sort of thing since it gets ALL props in one go?)
            objs[parent_name].props.update( dict([(k, Property(name=k, value=v, parent=objs[parent_name])) for k,v in line.iteritems() ]) )
            ret[ parent_name ] = objs[parent_name]
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












