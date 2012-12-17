from __future__ import with_statement
from django.conf import settings
import sys
import os
import time
from datetime import datetime, timedelta
#import re
import sh
import re
import logging
import configshell

from solarsan.utils import LoggedException, FormattedException
from solarsan.pretty import pp

from . import models as m
from . import tasks
from .utils import clean_name


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

    """
    Getters
    """

    def get_pool(self):
        if self.obj.type == 'pool':
            return self.obj
        else:
            return self.obj.pool

    def get_filesystem(self):
        if self.obj.type == 'pool':
            return self.obj.filesystem
        elif self.obj.type == 'filesystem':
            return self.obj

    """
    Child Creationism (Teach it to them young)
    """

    def ui_command_create_filesystem(self, name):
        '''
        create - Creates a Filesystem
        '''
        parent = self.get_filesystem()
        pool = self.get_pool()
        cls = m.Filesystem
        name = clean_name(name)

        obj_name = os.path.join(parent.name, name)
        obj = cls(name=obj_name)
        if obj.exists():
            raise LoggedException("Object '%s' already exists", name)
        obj.pool = pool
        obj.create()
        obj.save()

    def ui_command_create_volume(self, name, size):
        '''
        create - Creates a volume
        '''
        parent = self.get_filesystem()
        pool = self.get_pool()
        cls = m.Volume
        name = clean_name(name)

        obj_name = os.path.join(parent.name, name)
        obj = cls(name=obj_name)
        if obj.exists():
            raise LoggedException("Object '%s' already exists", name)
        obj.pool = pool
        obj.create(size)
        obj.save()

    def ui_command_create_snapshot(self, name):
        '''
        create - Creates a snapshot
        '''
        parent = self.get_filesystem()
        pool = self.get_pool()
        cls = m.Snapshot
        name = clean_name(name)

        obj_name = os.path.join(parent.name, name)
        obj = cls(name=obj_name)
        if obj.exists():
            raise LoggedException("Object '%s' already exists", name)
        obj.pool = pool
        obj.create()
        obj.save()

    def ui_command_destroy(self, confirm=False):
        obj = self.obj
        if not obj.exists():
            raise LoggedException("Object '%s' does not exist", obj)
        if not confirm:
            raise LoggedException("You must set confirm=True argument to confirm such an action of destruction")
        obj.destroy(confirm=confirm)
        obj.delete()

    def ui_command_rename(self, new):
        path = self.obj.path(len=-1)
        path.append(clean_name(new))
        new = os.path.join(*path)
        obj = self.obj
        if not obj.exists():
            raise LoggedException("Object '%s' does not exist", obj)
        obj.rename(new)


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

    """
    Devices
    """

    def ui_command_lsdevices(self):
        pp(self.obj.pretty_devices())

    def ui_command_add_device(self, path, type='disk'):
        logging.error("TODO")

    def ui_command_replace_device(self, old, new):
        logging.error("TODO")

    """
    Status
    """

    def ui_command_iostat(self, capture_length=2):
        pp(self.obj.iostat(capture_length=capture_length))

    def ui_command_status(self):
        status = self.obj.status()
        config = []
        for k, v in status['config'].items():
            v['name'] = k
            config.append(v)
        status['config'] = config
        pp(status)

    def ui_command_health(self):
        pp(self.obj.properties['health'])

    def ui_command_is_clustered(self):
        pp(self.obj.is_clustered)

    def ui_command_clear(self):
        pp(self.obj.clear())

    """
    Import/Export
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

    def ui_command_lsblk(self):
        os.system("lsblk")