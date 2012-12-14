from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
import os
import time
from datetime import datetime, timedelta
#import re
import sh
import logging
import configshell

from pprint import pprint as pp

from solarsan.utils import LoggedException, FormattedException

import storage.models
import storage.models as m
import storage.tasks
import status.tasks


class Command(BaseCommand):
    help = 'Run SolarSan Cli'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        main()


class CliRoot(configshell.node.ConfigNode):
    def __init__(self, shell):
        super(CliRoot, self).__init__('/', shell=shell)

        Storage(self)
        System(self)
        Logs(self)

        if settings.DEBUG:
            Developer(self)


class System(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(System, self).__init__('system', parent)

    def ui_command_hostname(self):
        '''
        Displays the system hostname
        '''
        os.system("hostname -f")

    def ui_command_uname(self):
        '''
        Displays the system uname information.
        '''
        os.system("uname -a")

    def ui_command_lsmod(self):
        '''
        lsmod - program to show the status of modules in the Linux Kernel
        '''
        os.system("lsmod")

    def ui_command_lspci(self):
        '''
        lspci - list all PCI devices
        '''
        os.system("lspci")

    def ui_command_lsusb(self):
        '''
        lsusb - list USB devices
        '''
        os.system("lsusb")

    def ui_command_lscpu(self):
        '''
        lscpu - CPU architecture information helper
        '''
        os.system("lscpu")

    def ui_command_uptime(self):
        '''
        uptime - Tell how long the system has been running.
        '''
        os.system("uptime")

    def ui_command_shutdown(Self):
        '''
        shutdown - Shutdown system
        '''
        status.tasks.shutdown.delay()

    def ui_command_reboot(Self):
        '''
        reboot - reboot system
        '''
        status.tasks.reboot.delay()

    def ui_command_check_services(self):
        os.system("initctl list | egrep 'solarsan|targetcli|mongo'")


#class


class StorageNode(configshell.node.ConfigNode):
    def __init__(self, parent, obj):
        self.obj = obj
        #self.parent = parent
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

                #max_child_depth = None
                show_depth = len(obj_path) + 1
                #children = []
                #while not children and (not max_child_depth or show_depth < max_child_depth):
                #    children = find_children(show_depth)
                children = find_children(show_depth)

                for child in children:
                    Dataset(self, child)

    def ui_command_create(self):
        '''
        create - Creates a storage Pool
        '''
        os.system("echo TODO")


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



class Pools(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Pools, self).__init__('pools', parent)

        for pool in storage.models.Pool.objects.all():
            Pool(self, pool)

    def ui_command_create(self):
        '''
        create - Creates a storage Pool
        '''
        os.system("echo TODO")


class Storage(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Storage, self).__init__('storage', parent)
        Pools(self)

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
        storage.tasks.sync_zfs.apply()


class Logs(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Logs, self).__init__('logs', parent)

    def ui_command_tail(self):
        '''
        tail - Tails syslog
        '''
        os.system("tail -qF /var/log/debug /var/log/syslog | ccze -A")


class Developer(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Developer, self).__init__('developer', parent)
        Benchmarks(self)

    def ui_command_shell(self):
        os.system("bash")

    def ui_command_pyshell(self):
        os.system("/opt/solarsanweb/manage shell_plus")

    def ui_command_ipyshell(self):
        os.system("/opt/solarsanweb/manage shell_plus --ipython")

    def ui_command_ipynotebook(self):
        os.system("/opt/solarsanweb/manage ipython notebook --ext=django_notebook")

    def ui_command_mongo(self):
        os.system("mongo")

    def ui_command_stop_services(self):
        os.system("stop solarsan")

    def ui_command_start_services(self):
        os.system("start solarsan")


class Benchmarks(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Benchmarks, self).__init__('benchmarks', parent)

    def ui_command_netperf(self, host=None):
        args = []
        if host:
            logging.info("Running client to host='%s'", host)
            args.extend(['-h', host])
        else:
            logging.info("Running server on 0.0.0.0")
        for line in sh.NPtcp(*args, _iter=True, _err_to_out=True):
            print line.rstrip("\n")

    test_pool = 'dpool'
    test_filesystem_name = '%(pool)s/omfg_test_benchmark'

    def _get_test_filesystem(self):
        pool = self.test_pool
        name = self.test_filesystem_name % {'pool': pool}
        try:
            fs = m.Filesystem.objects.get(name=name)
        except m.Filesystem.DoesNotExist:
            fs = m.Filesystem(name=name)
        return fs

    def _create_test_filesystem(self, atime='off', compress='on'):
        fs = self._get_test_filesystem()
        if fs.exists():
            logging.info("Destroying existing test filesystem '%s'", fs)
            fs.destroy(confirm=True)

        logging.info("Creating test filesystem '%s'", fs)
        fs.create()

        logging.info("Setting atime='%s' compress='%s'", atime, compress)
        fs.properties['atime'] = atime
        fs.properties['compress'] = compress

        logging.info("Changing ownership")
        sh.chown('nobody:nogroup', str(fs.properties['mountpoint']))

        return fs

    def _cleanup_test_filesystem(self, pool=None):
        if pool:
            self.test_pool = pool
        fs = self._get_test_filesystem()
        if not fs.exists():
            raise LoggedException("Could not destroy filesystem '%s' as it does not exist?", fs)
        logging.info("Destroying test filesystem '%s'", fs)
        fs.destroy(confirm=True)
        if fs.pk:
            fs.delete()

    def ui_command_cleanup(self, pool=None):
        if pool:
            self.test_pool = pool
        self._cleanup_test_filesystem()

    def ui_command_bonniepp(self, atime='off', compress='on', pool=None):
        if pool:
            self.test_pool = pool
        fs = self._create_test_filesystem(atime=atime, compress=compress)

        bonniepp = sh.Command('bonnie++')
        for line in bonniepp('-u', 'nobody', '-d', str(fs.properties['mountpoint']),
                             _iter=True, _err_to_out=True):
            print line.rstrip("\n")

        self._cleanup_test_filesystem()

    def ui_command_iozone(self, atime='off', compress='on', size='1M', pool=None):
        if pool:
            self.test_pool = pool
        fs = self._create_test_filesystem(atime=atime, compress=compress)

        cwd = os.curdir
        os.chdir(str(fs.properties['mountpoint']))

        try:
            with sh.sudo('-u', 'nobody', _with=True):
                for line in sh.iozone('-a', '-g', size, _iter=True, _err_to_out=True):
                    print line.rstrip("\n")
        finally:
            os.chdir(cwd)
        #os.chdir(cwd)
        logging.debug(os.curdir)
        time.sleep(1)

        self._cleanup_test_filesystem()


def main():
    shell = configshell.shell.ConfigShell('~/.solarsancli')
    root_node = CliRoot(shell)
    shell.run_interactive()

if __name__ == "__main__":
    main()
