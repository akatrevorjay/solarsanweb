""""
$ zfs/tree.py -- 'tree' object idea to show relations
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>

This way, we can have methods for each object, ie, tree.pools, pool.create_filesystem(), filesystem.create_snapshot()
It also makes caching much easier to implement and auto-reload, unlike a simple subclassed dict, as the methods are
  called each time it's accessed vs only when python decides to call __getitem__, so I believe it will solve the issues
  with my previous zfs object implementation while providing a nicer interface ;)
"""

#import time, datetime, logging, dateutil
#from django.utils import timezone
#from iterpipes import run, cmd, linecmd, check_call, format
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import os, time, logging
from solarsan.utils import FilterableDict

#from .pool import list as zpool_list
#from .dataset import list as zfs_list
#from .common import *

import pool
import dataset

"""
Tree
"""

class tree( FilterableDict ):
    """ Generate nice dict of parsed ZFS pools/datasets in a tree showing parent/child relationship """
    _lock_timeout = 10
    _locked = False
    def __init__( self, *args, **kwargs ):
        super( tree, self ).__init__( self, *args, **kwargs )
        self.refresh()
    def _check_if_locked( self ):
        """ Checks if we're locked and if so, waits until self.lock_timeout (default: 60) seconds before giving up """
        if self._locked == True:
                count = 0
                while self._locked == True:
                    time.sleep( 1 )
                    count += 1
                    if count > self._lock_timeout / 2:
                        logging.warning( "Halfway to timeout while waiting for lock to be released [timeout=%s]", self._lock_timeout )
                    elif count > self._lock_timeout:
                        raise Exception( 'Timed out while waiting for lock to be released [timeout=%s]' % self._lock_timeout )
#    def __getitem__( self, arg ):
#        """ Wrapper to check locks """
#        self._check_if_locked()
#        return super( tree, self ).__getitem__( arg )
#    def __setitem__( self, *args, **kwargs ):
#        """ Wrapper to check locks """
#        self._check_if_locked()
#        return super( tree, self ).__setitem__( self, *args, **kwargs )
    def refresh( self ):
        """ Generate nice dict of parsed ZFS pools/datasets in a tree showing parent/child relationship """
        self._check_if_locked()

        def add_objects_to_tree( *args ):
            """ Adds *args to tree; ets reused for any kind of object being added """
            for arg in args:
                for key, value in arg.items():
                    path = key.split( os.path.sep )
                    # If this is a snapshot, split the snapshot name from the filesytem name
                    if value['type'] == 'snapshot':     path.extend( path.pop().rsplit( '@', 1 ) )
                    # Go to base of tree
                    current_level = tree
                    # Snag relative name
                    name = path.pop()
                    # Move down the ladder
                    for part in path:
                        if not part in current_level:   current_level[part] = FilterableDict()
                        current_level = current_level[part]
                    # Apply dataset contents to pluralized dataset type, ie .snapshots
                    typelist = getattr( current_level, value['type'] + 's', FilterableDict() )
                    typelist[name] = value
                    setattr( current_level, value['type'] + 's', typelist )
                    # Set .has attribute
                    has = getattr( current_level, 'has', [] )
                    if not value['type'] + 's' in has:  has.append( value['type'] + 's' )
                    setattr( current_level, 'has', has )

        # Start tree, add pools
        tree = FilterableDict()
        add_objects_to_tree( pool.list(), dataset.list() )

        # Do a locked update
        try:
            self._check_if_locked()
            self._locked = True
            self.clear()
            self.update( tree )
            # hack
            setattr( self, 'has', getattr( tree, 'has' ) )
            for has in self.has: setattr( self, has, getattr( tree, has ) )
            self._locked = False
        except:
            raise Exception( "Could not do a locked update" )
        finally:
            self._locked = False

#"""
#Old Tree
#"""
#
#def tree():
#    datasets = zfs.list()
#    pools = zpool.list()
#    datasets = zfs.dataset.list()
#    tree = FilterableDict()
#
#    # Add pools
#    tree = dict(( (pk, {'pool': pv}) for pk, pv in pools.iteritems() ))
#
#    # Add datasets
#    for dk,dv in datasets.iteritems():
#        path = dk.split(os.path.sep)
#        if dv['type'] == 'snapshot':
#            (path[len(path) - 1], snapshot_name)  = path[len(path) - 1].rsplit('@', 1)
#
#        current_level = tree
#        for part in path:
#            if part not in current_level:
#                current_level[part] = {}
#            current_level = current_level[part]
#
#        if dv['type'] == 'snapshot':
#            if 'snapshots' not in current_level:
#                current_level['snapshots'] = {}
#            current_level['snapshots'][ snapshot_name ] = dv
#            current_level = current_level['snapshots']
#        else:
#            current_level[ '-'+dv['type'] ] = dv
#
#    return tree


