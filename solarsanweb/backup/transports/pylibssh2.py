
"""
SSH Stuffs
"""


from django.conf import settings
from select import select
import logging
import socket
import libssh2
import pipes


class SSHRemoteClientNonBlocking(object):
    LIBSSH2_ERROR_EAGAIN= -37

    def __init__(self, username, hostname, password, port=22, private_key=None, public_key=None):
        self.username = username
        self.hostname = hostname
        self.password = password
        self.port = port

        if private_key:
            self.private_key = private_key
            self.public_key = public_key or private_key + '.pub'

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(1)
        self.sock.connect_ex((self.hostname, self.port))
        self.sock.setblocking(0)

        self.session = libssh2.Session()
        self.session.setblocking(0)

    def _wait_select(self):
        '''
        Find out from libssh2 if its blocked on read or write and wait accordingly
        Return immediately if libssh2 is not blocked
        '''
        blockdir = self.session.blockdirections()
        if blockdir == 0:
            # return if not blocked
            return

        readfds = [self.sock] if (blockdir & 01) else []
        writefds = [self.sock] if (blockdir & 02) else []
        select(readfds, writefds, [])
        return

    def startup(self):
        return self.retry(self.session.startup, self.sock)

    def auth(self):
        order = ['agent', 'password']
        if getattr(self, 'private_key') and getattr(self, 'public_key'):
            order.insert(0, 'pubkey')

        def _auth(method):
            def auther(method):
                if method == 'agent':
                    return self.session.userauth_agent(self.username)
                elif method == 'pubkey':
                    return self.session.userauth_publickey_fromfile(
                        self.username,
                        self.public_key,
                        self.private_key,
                        self.password,
                        )
                elif method == 'password':
                    return self.session.userauth_password(self.username, self.password)
                else:
                    raise Exception("Unknown auth method specified: '%s'" % method)

            try:
                ret = self.retry(auther, method)
                return ret
            except Exception, e:
                logging.debug('Authentication failed using %s: %s', method, str(e))
                return False

        ret = self.retry(self.session.userauth_authenticated)
        if ret:
            return ret

        #return _auth('pubkey')

        while len(order) > 0:
            method = order.pop(0)

            ret = _auth(method)
            logging.debug('Authentication via %s: %s', method, ret)

            ret = self.retry(self.session.userauth_authenticated)
            if ret:
                return ret

        raise Exception('Exhausted all authentication methods')

    #def open_channel(self, pty=True):
    def open_channel(self):
        self.chan = self.session.open_session()
        count = 1
        while self.chan == None:
            count += 1
            self._wait_select()
            self.chan = self.session.open_session()
        #if pty:
        #    self.pty()
        return self.chan

    def __del__(self):
        return self.retry(self.session.close)

    def pty(self):
        return self.retry(self.chan.pty)

    ## TODO retry decorator
    def retry(self, func, *args, **kwargs):
        #logging.debug("ssh func='%s' args='%s' kwargs='%s'", func, args, kwargs)

        ret = func(*args, **kwargs)
        count = 1
        while ret == self.LIBSSH2_ERROR_EAGAIN:
            count += 1
            self._wait_select()
            ret = func(*args, **kwargs)

        #logging.debug("ssh func %s count %s", func, count)
        #logging.debug("ssh func %s ret %s", func, ret)
        return ret

    def read_channel_eof(self):
        ret = ''
        while not self.chan.eof():
            self._wait_select()
            data1 = self.chan.read_ex()
            while data1[0] > 0:
                #logging.debug('Received data')
                ret = ret + data1[1]
                data1 = self.chan.read_ex()
        return ret

    def execute(self, *args, **kwargs):
        ''' run a command on the remote host '''
        self.open_channel()

        if kwargs.get('quoted'):
            args = map(lambda x: pipes.quote(x), args)

        cmd = ' '.join(args)

        if kwargs.get('shell'):
            cmd = kwargs['shell'] + cmd

        return self.retry(self.chan.execute, cmd)

    def execute_shell(self, *args, **kwargs):
        ''' run a command on the remote host '''
        kwargs['shell'] = kwargs.get('shell', '"$SHELL" -c')
        return self.execute(*args, **kwargs)
