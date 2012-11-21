

from backup.util import run_command, progressbar, CalledProcessError
from backup.transports.pylibssh2 import SSHRemoteClientNonBlocking
from backup.backup_zfs import PoolSet
import os
import subprocess
import logging
#import io

## pipes are very, very slow using pbs/sh
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

    """ FAR TOO SLOW, sh/pbs EATS RAM/CPU FOR BREAKFAST
    def transfer_sh(self, dest_conn,
                 s, d,
                 send_opts=None, receive_opts=None,
                 bufsize=0):
        if not send_opts:
            send_opts = []
        if not receive_opts:
            receive_opts = []

        zfs_send = sh.zfs.bake('send', '-Rv')
        ssh_dest = sh.ssh.bake('root@192.168.122.167', '-i', '/opt/solarsanweb/conf/id_rsa', '-C', '--')
        ssh_zfs_recv = ssh_dest.bake('zfs', 'receive', '-Fuv')

        send_opts.append(s)
        receive_opts.append(d)

        dest_conn._dirty = True

        for line in ssh_zfs_recv(zfs_send(*send_opts,
                                          _piped=True,
                                          #_out_bufsize=bufsize,
                                          #_out_bufsize=512 * 1024,
                                          _out_bufsize=0,
                                          #_internal_bufsize=1,
                                          _tty_out=False),
                                 *receive_opts,
                                 #_tty_in=False,
                                 #_in_bufsize=512 * 1024,
                                 #_out_bufsize=1,
                                 #_internal_bufsize=1,
                                 _iter=True):
            line = line.rsplit("\n")[0]
            logging.debug('repl: %s', line)
    """

    #
    #def transfer(self, dest_conn, s, d, fromsnapshot=None, bufsize=-1, send_opts=None, receive_opts=None):
    #    src_conn = self
    #
    #    if send_opts is None:
    #        send_opts = []
    #    if receive_opts is None:
    #        receive_opts = []
    #    fromsnapshot = fromsnapshot and ['-i', fromsnapshot] or []
    #
    #    send = src_conn.send(s, opts=[] + fromsnapshot + send_opts)
    #    recv = dest_conn.receive(d, opts=['-Fu'] + receive_opts)
    #
    #    dest_conn._dirty = True
    #    #self.ssh.session.setblocking(1)
    #
    #    while True:
    #        sendbuf_out = send.stdout.read(self.bufsize)
    #        if sendbuf_out != '':
    #            self.ssh.chan.write(sendbuf_out)
    #
    #        sendbuf_err = send.stderr.read(self.bufsize)
    #
    #
    #        time.sleep(0.1)
    #
    #    print "Done with loop"
    #
    #    #print self.ssh.read_channel_eof()
    #    #self.ssh.chan.send_eof()
    #
    #    #self.ssh.session.setblocking(0)
    #
    #    os.kill(send.pid, 15)
    #




    #def transfer2(self, dest_conn, s, d, fromsnapshot=None, bufsize=-1, send_opts=None, receive_opts=None):
    #    src_conn = self
    #
    #    if send_opts is None:
    #        send_opts = []
    #    if receive_opts is None:
    #        receive_opts = []
    #    fromsnapshot = fromsnapshot and ['-i', fromsnapshot] or []
    #
    #    try:
    #        send = src_conn.send(s, opts=[] + fromsnapshot + send_opts)
    #        # Launch async readers for stdout/stder
    #        #send_stdout_queue = Queue.Queue()
    #        #send_stdout_reader = AsynchronousFileReader(send.stdout, send_stdout_queue)
    #        #send_stdout_reader.start()
    #        send_stderr_queue = Queue.Queue()
    #        send_stderr_reader = AsynchronousFileReader(send.stderr, send_stderr_queue)
    #        send_stderr_reader.start()
    #
    #        recv = dest_conn.receive(d, opts=['-Fu'] + receive_opts)
    #        # Launch async readers for stdout/stder
    #        recv_stdout_queue = Queue.Queue()
    #        recv_stdout_reader = AsynchronousFileReader(self.ssh.chan, recv_stdout_queue)
    #        recv_stdout_reader.start()
    #        #recv_stderr_queue = Queue.Queue()
    #        #recv_stderr_reader = AsynchronousFileReader(process.stderr, recv_stderr_queue)
    #        #recv_stderr_reader.start()
    #
    #        while not recv_stdout_reader.eof() or not send_stderr_reader.eof():
    #        #while True:
    #            #while not send_stderr_queue.empty():
    #            if not send_stderr_queue.empty():
    #                line = send_stderr_queue.get()
    #                print 'send: err: ' + repr(line)
    #
    #            #while not recv_stdout_queue.empty():
    #            if not recv_stdout_queue.empty():
    #                line = recv_stdout_queue.get()
    #                print 'recv: out: ' + repr(line)
    #
    #
    #
    #            # Sleep a bit before asking the readers again.
    #            time.sleep(.1)
    #
    #        # Let's be tidy and join the threads we've started.
    #        send_stderr_reader.join()
    #        recv_stdout_reader.join()
    #
    #        # Close subprocess' file descriptors.
    #        #process.stdout.close()
    #        #process.stderr.close()
    #
    #
    #    finally:
    #        os.kill(send.pid, 15)
    #        raise
