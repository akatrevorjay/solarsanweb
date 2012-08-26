""""
$ zfs/cmd.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

import logging
import iterpipes
import yaml

"""
User vars
"""

PATHS = {'zfs':     "/sbin/zfs",
         'zpool':   "/sbin/zpool",
         'zdb':     "/sbin/zdb",
         }


"""
Command Handling
"""

def _cmd(cmd, *args):
    """ Returns a prepped linecmd """
    # Black magic
    cmdf = PATHS[cmd]+' '+' '.join([ ('{}') for i in range(len(args)) ])
    logging.debug("zfs.cmd: %s %s", cmd, args)
    return iterpipes.linecmd(cmdf, *args)


def zpool(*args):
    """ Returns linecmd for zpool execution """
    return _cmd('zpool', *args)


def zfs(*args):
    """ Returns linecmd for zfs execution """
    return _cmd('zfs', *args)


def zdb(*args):
    """ Returns linecmd for zdb execution """
    return _cmd('zdb', *args)



"""

Command/Filter API:

if bool(PoolCommand('status', 'rpool', ofilter=YamlFilter)):
    print "y"

rv = int(PoolCommand('status', 'rpool', ofilter=YamlFilter)):

ret = PoolCommand('status', 'rpool', ofilter=YamlFilter)

"""

class Command(object):
    """ Command Base """
    def __init__(self, *args, **kwargs):
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        self.initial_args = args
        ofilter = kwargs.get('ofilter', None)
        if ofilter:
            self.ofilter = ofilter

    def _checks(self, *args, **kwargs):
        if not getattr(self, 'cmd', None):
            if 'cmd' in kwargs:
                self.cmd = kwargs['cmd']
            else:
                raise Exception("Command path is not set for '%s'. If this is not a subclass, try kwargs['cmd']." % self)

    def __call__(self, *args, **kwargs):
        """ Executes command with args, returns data as specified by kwarg['format'] """
        if not isinstance(args, list):
            args = isinstance(args, basestring) and [args] or isinstance(args, tuple) and list(args)
        if getattr(self, 'initial_args', None):
            args = self.initial_args + args
        self._checks(*args, **kwargs)

        # Generate command arg mask from *args with some black pymagic
        cmdf = self.cmd+' '+' '.join(['{}' for i in xrange(len(args))])
        logging.debug("Command: %s", self)
        print "Command: %s %s %s %s" % (self, self.cmd, args, kwargs)

        ofilter = kwargs.pop('ofilter', getattr(self, 'ofilter', None))
        ret_type = kwargs.pop('ret', None)
        binary = kwargs.pop('binary', True)

        mkcmd = binary and iterpipes.bincmd or iterpipes.linecmd
        itercmd = mkcmd(cmdf, *args, **kwargs)

        ret = ''
        if ret_type == bool:
            return iterpipes.check_call(iterpipes.bincmd(cmdf, *args, **kwargs))

        elif ret_type == int:
            return iterpipes.call(iterpipes.bincmd(cmdf, *args, **kwargs))

        else:
            for buf in iterpipes.run(itercmd):
                ret += str(buf)
            if ofilter:
                ret = ofilter.load(ret)
            return ret

    def __bool__(self):
        return self.__call__(ret=bool)

    def __int__(self):
        return self.__call__(ret=int)


class ZPoolCommand(Command):
    """ Runs zpool with specified *args """
    cmd = PATHS['zpool']

class ZfsCommand(Command):
    cmd = PATHS['zfs']

class ZdbCommand(Command):
    cmd = PATHS['zdb']

"""
Filters
"""

#@filter.register
class Filter(object):
    """ Filter Base """
    @classmethod
    def load(self, data):
        raise Exception('No load method found for filter %s', self)
    @classmethod
    def dump(self, data):
        raise Exception('No dump method found for filter %s', self)
    #def __call__(self, data, *args, **kwargs):
    #    raise Exception("No __call__ method found for parser '%s'", self)

#@filter.register
class NullFilter(object):
    """ Null Filter, does nothing but give you back your data """
    @classmethod
    def load(self, data):
        return data
    dumps = load

#@filter.register
class SafeYamlFilter(Filter):
    """ YAML Filter """
    @classmethod
    def load(self, data):
        return yaml.safe_load(data)
    @classmethod
    def dump(self, data):
        return yaml.safe_dump(data)


"""
Parsers
"""

#@parser.register
class Parser(object):
    """ Parser Base """
    def __call__(self, data, *args, **kwargs):
        raise Exception("No __call__ method found for parser '%s'", self)


#@parser.register
class NullParser(Parser):
    """ Null Filter, does nothing but give you back your data """
    def __call__(self, data, *args, **kwargs):
        return data


#@parser.register
class ZfsSpaceDelimWithHeaderParser(Parser):
    pass


#@parser.register
class ZfsMachineReadableParser(Parser):
    pass


#@parser.register
class ZdbYamlParser(Parser):
    pass


#@parser.register
class ZdbDatasetParser(Parser):
    pass
