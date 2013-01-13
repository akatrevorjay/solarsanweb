import os
import logging
import time

import configshell
from configshell import ConfigNode, ExecutionError
import sh

from pprint import pprint as pp
from solarsan.utils import LoggedException, FormattedException

from django.conf import settings
import status.tasks
import cluster.tasks

import storage.models as m



class System(ConfigNode):
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

    def ui_command_shutdown(self):
        '''
        shutdown - Shutdown system
        '''
        status.tasks.shutdown.delay()

    def ui_command_reboot(self):
        '''
        reboot - reboot system
        '''
        status.tasks.reboot.delay()

    def ui_command_check_services(self):
        os.system("initctl list | egrep 'solarsan|targetcli|mongo'")


"""
Developer
"""


class Developer(ConfigNode):
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

    def ui_command_targetcli(self):
        os.system("targetcli")

    def ui_command_export_clustered_pool_vdevs(self):
        cluster.tasks.export_clustered_pool_vdevs.apply()

    def ui_command_top(self):
        os.system("top")

    def ui_command_ps(self):
        os.system("ps aux")

    def ui_command_pstree(self):
        os.system("pstree -ahuU")

    def ui_command_iostat(self):
        os.system("iostat -m 5 2")

    def ui_command_zpool_iostat(self):
        os.system("zpool iostat -v 5 2")

    def ui_command_ibstat(self):
        os.system("ibstat")

    def ui_command_ibstatus(self):
        os.system("ibstatus")

    def ui_command_ibv_devinfo(self):
        os.system("ibv_devinfo")

    def ui_command_ibping(self, host):
        print sh.ibping(host, _err_to_out=True)

    def ui_command_ibrouters(self):
        os.system("ibrouters")

    def ui_command_ibswitches(self):
        os.system("ibswitches")

    def ui_command_ibdiscover(self):
        os.system("ibdiscover")

    def ui_command_ibnodes(self):
        os.system("ibnodes")

    def ui_command_ibtool(self, *args):
        for line in sh.ibtool(*args, _iter=True, _err_to_out=True):
            print line.rstrip("\n")

    def ui_command_rdma(self, host=None):
        if host:
            logging.info("Running client to host='%s'", host)
            ret = sh.rdma_client(host, _err_to_out=True, _iter=True)
        else:
            logging.info("Running server on 0.0.0.0")
            ret = sh.rdma_server(_err_to_out=True, _iter=True)
        for line in ret:
            print line.rstrip("\n")

    #def ui_command_ibstat(self):
    #    os.system("ibstat")

    #def ui_command_ibstat(self):
    #    os.system("ibstat")

    def ui_command_ipdb(self):
        import ipdb
        ipdb.set_trace()

    #def ui_command_ipdb_post_mortem(self):
    #    import ipdb
    #    ipdb.pm()


class Benchmarks(ConfigNode):
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


class CliRoot(ConfigNode):
    def __init__(self, shell, sections):
        super(CliRoot, self).__init__('/', shell=shell)

        self.define_config_group_param(
            'global', 'developer_mode', 'bool',
            'If true, enables developer mode.')
        #print self.get_group_param('global', 'developer_mode')


        for section in sections:
            section(self)

        System(self)

        if settings.DEBUG:
            Developer(self)

    def summary(self):
        #return ('Thar be dragons.', False)
        return ('Ready.', True)

    def new_node(self, new_node):
        logging.info("New node: %s", new_node)
        return None

    def refresh(self):
        for child in self.children:
            child.refresh()

    def ui_command_refresh(self):
        self.refresh()

    #def ui_getgroup_global(self, key):
    #    '''
    #    This is the backend method for getting keys.
    #    @key key: The key to get the value of.
    #    @type key: str
    #    @return: The key's value
    #    @rtype: arbitrary
    #    '''
    #    logging.info("attr=%s", key)
    #    #return self.rtsnode.get_global(key)

    #def ui_setgroup_global(self, key, value):
    #    '''
    #    This is the backend method for setting keys.
    #    @key key: The key to set the value of.
    #    @type key: str
    #    @key value: The key's value
    #    @type value: arbitrary
    #    '''
    #    logging.info("attr=%s val=%s", key, value)
    #    #self.assert_root()
    #    #self.rtsnode.set_global(key, value)

    def ui_getgroup_param(self, param):
        '''
        This is the backend method for getting params.
        @param param: The param to get the value of.
        @type param: str
        @return: The param's value
        @rtype: arbitrary
        '''
        logging.info("attr=%s", param)
        #return self.rtsnode.get_param(param)

    def ui_setgroup_param(self, param, value):
        '''
        This is the backend method for setting params.
        @param param: The param to set the value of.
        @type param: str
        @param value: The param's value
        @type value: arbitrary
        '''
        logging.info("attr=%s val=%s", param, value)
        #self.assert_root()
        #self.rtsnode.set_param(param, value)

    def ui_getgroup_attribute(self, attribute):
        '''
        This is the backend method for getting attributes.
        @param attribute: The attribute to get the value of.
        @type attribute: str
        @return: The attribute's value
        @rtype: arbitrary
        '''
        logging.info("attr=%s", attribute)
        #return self.rtsnode.get_attribute(attribute)

    def ui_setgroup_attribute(self, attribute, value):
        '''
        This is the backend method for setting attributes.
        @param attribute: The attribute to set the value of.
        @type attribute: str
        @param value: The attribute's value
        @type value: arbitrary
        '''
        logging.info("attr=%s val=%s", attribute, value)
        #self.assert_root()
        #self.rtsnode.set_attribute(attribute, value)

    def ui_getgroup_parameter(self, parameter):
        '''
        This is the backend method for getting parameters.
        @param parameter: The parameter to get the value of.
        @type parameter: str
        @return: The parameter's value
        @rtype: arbitrary
        '''
        logging.info("parameter=%s", parameter)
        #return self.rtsnode.get_parameter(parameter)

    def ui_setgroup_parameter(self, parameter, value):
        '''
        This is the backend method for setting parameters.
        @param parameter: The parameter to set the value of.
        @type parameter: str
        @param value: The parameter's value
        @type value: arbitrary
        '''
        logging.info("parameter=%s val=%s", parameter, value)
        #self.assert_root()
        #self.rtsnode.set_parameter(parameter, value)


from storage.cli import Storage
from logs.cli import Logs
from configure.cli import Configure
from cluster.cli import Cluster


def main():
    CLI_TOP_SECTIONS = [Storage, Logs, Configure, Cluster]

    shell = configshell.shell.ConfigShell('~/.solarsancli')
    root_node = CliRoot(shell, CLI_TOP_SECTIONS)
    shell.run_interactive()

if __name__ == "__main__":
    main()
