""""
$ zfs.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

from .cmd import zfs_destroy, zfs_list, zfs_snapshot
from .cmd import zpool_iostat, zpool_list
from .tree import tree, tree_obj

