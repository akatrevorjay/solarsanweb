""""
$ zfs.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

# old
import pool
import dataset
from tree import tree

# new
from objects import Pool, Dataset, Filesystem, Volume, Snapshot
import cmd

