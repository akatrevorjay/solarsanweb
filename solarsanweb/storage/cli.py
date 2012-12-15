from __future__ import with_statement
from django.conf import settings
import sys
import os
import time
from datetime import datetime, timedelta
#import re
import sh
import logging
import configshell

from solarsan.utils import LoggedException, FormattedException
from pprint import pprint, pformat

from . import models as m
from . import tasks


from pygments import highlight
from pygments.lexers import PythonLexer
#from pygments.lexers.web import JSONLexer
from pygments.formatters.terminal256 import Terminal256Formatter


def pp(arg):
    print highlight(pformat(arg), PythonLexer(), Terminal256Formatter())
    #print highlight(pformat(arg), JSONLexer(), Terminal256Formatter())


class StorageNode(configshell.node.ConfigNode):
    def __init__(self, parent, obj):
        self.obj = obj
        obj_path = obj.path()
        super(StorageNode, self).__init__(obj_path[-1], parent)

        if hasattr(obj, 'children'):
            all_children = obj.children()
            if all_children:
                def find_children(depth):
                    ret = []
                    for child in all_children:
                        child_path = child.path()
                        child_depth = len(child_path)
                        #if child_depth > max_child_depth:
                        #    max_child_depth = child_depth
                        if child_depth == depth:
                            ret.append(child)
                    return ret

                show_depth = len(obj_path) + 1
                children = find_children(show_depth)

                for child in children:
                    add_child_dataset(self, child)

    def ui_command_create_filesystem(self):
        '''
        create - Creates a Filesystem
        '''
        os.system("echo TODO")

    def ui_command_create_volume(self):
        '''
        create - Creates a volume
        '''
        os.system("echo TODO")

    def ui_command_create_snapshot(self):
        '''
        create - Creates a snapshot
        '''
        os.system("echo TODO")


def add_child_dataset(self, child):
    if child.type == 'filesystem':
        Dataset(self, child)
    elif child.type == 'volume':
        Dataset(self, child)
    elif child.type == 'snapshot':
        Dataset(self, child)


class StorageNodeChildType(configshell.node.ConfigNode):
    def __init__(self, parent, child_type):
        self.child_type = child_type
        super(StorageNodeChildType, self).__init__('%ss' % child_type, parent)


class Dataset(StorageNode):
    def __init__(self, parent, dataset):
        super(Dataset, self).__init__(parent, dataset)


class Pool(StorageNode):
    def __init__(self, parent, pool):
        super(Pool, self).__init__(parent, pool)

    def ui_command_iostat(self, capture_length=2):
        pp(self.obj.iostat(capture_length=capture_length))

    def ui_command_status(self):
        status = self.obj.status()
        status['config'] = dict(status['config'])
        pp(status)

    def ui_command_clear(self):
        pp(self.obj.clear())

    """
    Developer
    """

    def ui_command_import(self):
        pp(self.obj.import_())

    def ui_command_export(self):
        pp(self.obj.export())



class Storage(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Storage, self).__init__('storage', parent)

        for pool in m.Pool.objects.all():
            Pool(self, pool)

    def ui_command_create_pool(self, name):
        '''
        create - Creates a storage Pool
        '''
        os.system("echo TODO")

    def ui_command_lsscsi(self):
        '''
        lsscsi - list SCSI devices (or hosts) and their attributes
        '''
        os.system("lsscsi")

    def ui_command_df(self):
        '''
        df - report file system disk space usage
        '''
        os.system("df -h")

    def ui_command_sync_zfs(self):
        '''
        sync_metadata - syncs metadata from filesystem to database
        '''
        tasks.sync_zfs.apply()
