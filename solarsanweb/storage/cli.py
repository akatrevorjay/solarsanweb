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
from configshell import ConfigNode, ExecutionError

from solarsan.utils import LoggedException, FormattedException, \
    convert_human_to_bytes, convert_bytes_to_human
from solarsan.pretty import pp

from . import models as m
from . import tasks
from .utils import clean_name


class StorageNode(ConfigNode):
    def __init__(self, parent, obj):
        self.obj = obj
        obj_path = obj.path()
        super(StorageNode, self).__init__(obj_path[-1], parent)

        self.define_config_group_param(
            'property', 'compress', 'string',
            'If on, enables compression.')

        self.define_config_group_param(
            'property', 'dedup', 'string',
            'If on, enables deduplication.')

        self.define_config_group_param(
            'property', 'atime', 'string',
            'If on, enables updates of file access times. This hurts performance, and is rarely wanted.')

        self.define_config_group_param(
            'statistic', 'compressratio', 'string',
            'Compression ratio for this dataset and children.')

        self.define_config_group_param(
            'statistic', 'dedupratio', 'string',
            'Deduplication ratio for this dataset and children.')

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

    """
    Properties
    """

    POOL_PROPERTIES = []

    def ui_getgroup_property(self, property):
        '''
        This is the backend method for getting propertys.
        @param property: The property to get the value of.
        @type property: str
        @return: The property's value
        @rtype: arbitrary
        '''
        if property in self.POOL_PROPERTIES:
            obj = self.get_pool()
        else:
            obj = self.get_filesystem()
        return str(obj.properties[property])

    def ui_setgroup_property(self, property, value):
        '''
        This is the backend method for setting propertys.
        @param property: The property to set the value of.
        @type property: str
        @param value: The property's value
        @type value: arbitrary
        '''
        if property in self.POOL_PROPERTIES:
            obj = self.get_pool()
        else:
            obj = self.get_filesystem()
        obj.properties[property] = value

    POOL_STATISTICS = ['dedupratio']

    def ui_getgroup_statistic(self, statistic):
        '''
        This is the backend method for getting statistics.
        @param statistic: The statistic to get the value of.
        @type statistic: str
        @return: The statistic's value
        @rtype: arbitrary
        '''
        if statistic in self.POOL_STATISTICS:
            obj = self.get_pool()
        else:
            obj = self.get_filesystem()

        return str(obj.properties[statistic])

    def ui_setgroup_statistic(self, statistic, value):
        '''
        This is the backend method for setting statistics.
        @param statistic: The statistic to set the value of.
        @type statistic: str
        @param value: The statistic's value
        @type value: arbitrary
        '''
        #self.obj.properties[statistic] = value
        return None



def add_child_dataset(self, child):
    if child.type == 'filesystem':
        Dataset(self, child)
    elif child.type == 'volume':
        Dataset(self, child)
    elif child.type == 'snapshot':
        Dataset(self, child)


class StorageNodeChildType(ConfigNode):
    def __init__(self, parent, child_type):
        self.child_type = child_type
        super(StorageNodeChildType, self).__init__('%ss' % child_type, parent)


class Dataset(StorageNode):
    def __init__(self, parent, dataset):
        super(Dataset, self).__init__(parent, dataset)


    #def ui_type_blah(self):
    #    pass

    def summary(self):
        # TODO Check disk usage percentage, generic self.obj.errors/warnings
        # interface perhaps?
        return (self.obj.type, True)


class Pool(StorageNode):
    help_intro = '''
                 STORAGE POOL
                 ============
                 Storage Pools are dataset containers, they contain datasets such as a filesystem or a volume.

                 Literally, it's just like a giant swimming pool for your data.
                 That is, except someone replaced your water with solid state drives and rotating platters.
                 '''

    def __init__(self, parent, pool):
        super(Pool, self).__init__(parent, pool)

    def summary(self):
        return (self.obj.health, self.obj.is_healthy())

    def ui_command_usage(self):
        obj = self.obj
        alloc = str(obj.properties['alloc'])
        free = str(obj.properties['free'])
        total = str(obj.properties['size'])
        ret = {'alloc': alloc,
               'free': free,
               'total': total,
               }
        pp(ret)

    """
    Devices
    """

    def ui_command_lsdevices(self):
        pp(self.obj.pretty_devices())

    #def ui_command_add_device(self, path, type='disk'):
    #    logging.error("TODO")

    #def ui_command_replace_device(self, old, new):
    #    logging.error("TODO")

    """
    Status
    """

    def ui_command_iostat(self, capture_length=2):
        pp(self.obj.iostat(capture_length=capture_length))

    def ui_command_status(self):
        status = self.obj.status()
        #config = []
        #for k, v in status['config'].items():
        #    v['name'] = k
        #    config.append(v)
        #status['config'] = config
        status.pop('config')
        pp(status)

    def ui_command_health(self):
        pp(str(self.obj.properties['health']))

    def ui_command_clear(self):
        pp(self.obj.clear())

    """
    Import/Export
    """

    def ui_command_import(self):
        pp(self.obj.import_())

    def ui_command_export(self):
        pp(self.obj.export())

    """
    Cluster
    """

    # TODO Attribute
    def ui_command_is_clustered(self):
        pp(self.obj.is_clustered)


class Storage(ConfigNode):
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
