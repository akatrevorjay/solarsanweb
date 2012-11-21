

from backup.util import run_command, progressbar, CalledProcessError
from backup.transports.pylibssh2 import SSHRemoteClientNonBlocking
from backup.backup_zfs import PoolSet
import os
import subprocess
import logging
#import io
#import sh


class ZFSConnection(object):

    local = False
    _dirty = True

    def __init__(self, **kwargs):
        self.hostname = kwargs.get('hostname', 'localhost')
        self.bufsize = kwargs.pop('bufsize', -1)

        self._poolset = PoolSet()
        self.command = ['zfs']

        self.local = self.hostname in ['localhost', '127.0.0.1']
        if self.local:
            return

        self.ssh = SSHRemoteClientNonBlocking(**kwargs)
        self.ssh.startup()
        self.ssh.auth()
        self.ssh.open_channel()

        # TODO Unfortunately I haven't worked through all of the issues with libssh2 and subprocess yet.
        #       It 'works for me', but needs more testing. Until then use standard subprocess pipes for
        #       The actual send/receive transport ~trevorj 090312
        self.ssh_command = ['ssh',
                            '-o', 'BatchMode=yes',
                            '-a', '-x',
                            '-c', 'arcfour',
                            '-p', str(self.ssh.port),
                            '-l', self.ssh.username,
                            '-i', self.ssh.private_key,
                            self.ssh.hostname]

    def _cmd(self, command):
        if self.local:
            (stdout, stderr) = run_command(command)
            return (stdout, stderr)
        else:
            self.ssh.open_channel()
            self.ssh.execute(*command)
            stdout = self.ssh.read_channel_eof()
            rc = self.ssh.chan.exit_status()
            if rc == 0:
                return (stdout, '')
            else:
                #command = self.ssh._execute_cmd(command)
                raise subprocess.CalledProcessError(rc, command, stdout)

    def _get_poolset(self):
        if self._dirty:
            (stdout, stderr) = self._cmd(self.command + ['list', '-r', '-t',
                                                         'all', '-H'])
            (stdout2, stderr2) = self._cmd(self.command + [
                                           'get', '-r', '-o', 'name,value',
                                           'creation', '-Hp'])
            self._poolset.parse_zfs_r_output(stdout, stdout2)
            self._dirty = False
        return self._poolset

    pools = property(_get_poolset)

    def create_dataset(self, name):
        self._cmd(self.command + ['create', '-o', 'mountpoint=none', name])
        self._dirty = True
        return self.pools.lookup(name)

    def destroy(self, name):
        self._cmd(self.command + ['destroy', '-r', name])
        self._dirty = True

    def snapshot_recursively(self, name, snapshotname):
        self._cmd(self.command + ['snapshot', '-r', '%s@%s' % (name,
                                                               snapshotname)])
        self._dirty = True

    def send(self, name, opts=None, bufsize=-1, compression=False):
        if not opts:
            opts = []
        cmd = self.command + ['send'] + opts + [name]
        if not self.local:
            ssh_command = self.ssh_command
            if compression:
                ssh_command.append('-C')
            cmd = ssh_command + cmd
        logging.debug("Executing command '%s'", cmd)

        p = subprocess.Popen(cmd, stdin=file(os.devnull, 'r'),
                             stdout=subprocess.PIPE, bufsize=self.bufsize)
        return p

    def receive(self, name, pipe, opts=None, bufsize=-1, compression=False):
        if not opts:
            opts = []
        cmd = self.command
        if not self.local:
            ssh_command = self.ssh_command
            if compression:
                ssh_command.append('-C')
            cmd = ssh_command + cmd

        cmd = cmd + ['receive'] + opts + [name]
        logging.debug("Executing command '%s'", cmd)

        # TODO Finalize libssh2 send/receive
        #self.ssh.execute(*cmd)

        p = subprocess.Popen(cmd, stdin=pipe,
                             bufsize=self.bufsize)
        return p

    def transfer(self, dest_conn, s, d, fromsnapshot=None, showprogress=False, bufsize=-1,
                 send_opts=None, receive_opts=None, ratelimit=-1, compression=True):
        src_conn = self

        if send_opts is None:
            send_opts = []
        if receive_opts is None:
            receive_opts = []

        if fromsnapshot:
            fromsnapshot = ['-i', fromsnapshot]
        else:
            fromsnapshot = []
        sndprg = src_conn.send(s, opts=[] + fromsnapshot + send_opts,
                               bufsize=self.bufsize, compression=compression)

        if showprogress:
            try:
                barprg = progressbar(pipe=sndprg.stdout,
                                     bufsize=self.bufsize,
                                     ratelimit=ratelimit)
            except OSError:
                os.kill(sndprg.pid, 15)
                raise
        else:
            barprg = sndprg

        try:
            rcvprg = dest_conn.receive(d, pipe=barprg.stdout,
                                       opts=['-Fu'] + receive_opts,
                                       bufsize=self.bufsize,
                                       compression=compression)
        except OSError:
            os.kill(sndprg.pid, 15)
            if sndprg.pid != barprg.pid:
                os.kill(barprg.pid, 15)
            raise

        dest_conn._dirty = True
        ret = sndprg.wait()
        if ret:
            os.kill(rcvprg.pid, 15)
            if sndprg.pid != barprg.pid:
                os.kill(barprg.pid, 15)
            raise CalledProcessError(ret, ['zfs', 'send'])

        ret2 = rcvprg.wait()
        if ret2:
            if sndprg.pid != barprg.pid:
                os.kill(barprg.pid, 15)
            raise CalledProcessError(ret2, ['zfs', 'receive'])

        if sndprg.pid != barprg.pid:
            ret3 = barprg.wait()
            if ret3:
                raise CalledProcessError(ret3, ['clpbar'])
