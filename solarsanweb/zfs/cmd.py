""""
$ zfs/cmd.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

import logging
import iterpipes


"""
User vars
"""

paths = {'zfs':     "/sbin/zfs",
         'zpool':   "/sbin/zpool",
         'zdb':     "/sbin/zdb",
         }


"""
Command Handling
"""

def _cmd(cmd, *zargs):
    """ Returns a prepped linecmd """
    # Black magic
    cmdf = paths[cmd]+' '+' '.join([ ('{}') for i in range(len(zargs)) ])
    logging.debug("zfs.cmd: %s %s", cmd, zargs)
    return iterpipes.linecmd(cmdf, *zargs)


def zpool(*zargs):
    """ Returns linecmd for zfs execution """
    return _cmd('zpool', *zargs)


def zfs(*zargs):
    """ Returns linecmd for zfs execution """
    return _cmd('zfs', *zargs)


def zdb(*zargs):
    """ Returns linecmd for zdb execution """
    return _cmd('zdb', *zargs)
