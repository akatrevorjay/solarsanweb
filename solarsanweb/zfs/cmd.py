""""
$ zfs/cmd.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

import logging
import iterpipes
import yaml
import re
#from solarsan.utils import args_list

"""
User vars
"""

PATHS = {'zfs':     "/sbin/zfs",
         'zpool':   "/sbin/zpool",
         'zdb':     "/sbin/zdb",
         }

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
        self._checks(*args, **kwargs)

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
        logging.debug("Command: %s %s %s %s", self, self.cmd, args, kwargs)
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
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, data, *args, **kwargs):
        raise Exception("No __call__ method found for parser '%s'", self)


#@parser.register
class NullParser(Parser):
    """ Null Filter, does nothing but give you back your data """
    def __call__(self, data, *args, **kwargs):
        return data


"""
Command Handling
"""

def _cmd(cmd, *args, **kwargs):
    """ Returns a prepped linecmd """
    kwargs['cmd'] = cmd
    cmd = Command(*args, **kwargs)
    return cmd()


def zpool(*args, **kwargs):
    """ Returns linecmd for zpool execution """
    cmd = ZPoolCommand(*args, **kwargs)
    return cmd()


def zfs(*args, **kwargs):
    """ Returns linecmd for zfs execution """
    cmd = ZfsCommand(*args, **kwargs)
    return cmd()


def zdb(*args, **kwargs):
    """ Returns linecmd for zdb execution """
    cmd = ZdbCommand(*args, **kwargs)
    return cmd()




class RegexParser(Parser):
    def __init__(self, expression, **kwargs):
        self.expression = expression
        self.initial_kwargs = kwargs
        super(RegexParser, self).__init__(**kwargs)
    def __call__(self, *data, **kw):
        kwargs = self.initial_kwargs.copy()
        kwargs.update(kw)

        if not isinstance(data, list):
            data = isinstance(data, basestring) and [data] or isinstance(data, tuple) and list(data)
        if len(data) == 1:
            data = data[0].splitlines()

        group_by = kwargs.get('group_by', 'group_by')
        strict = kwargs.get('strict')
        expression = kwargs.get('expression', getattr(self, 'expression'))
        linere = re.compile(expression)

        if 'group_by' in linere.groupindex:
            ret = {}
        else:
            ret = []

        skip = kwargs.get('skip', 0)
        skipped = 0
        for line in data:
            if skipped < skip:
                skipped += 1
                continue

            m = linere.match(line)
            if not m:
                error = "Unable to parse line '%s'" % line
                logging.error(error)
                if strict:
                    raise Exception("%s and strict is in effect" % error)
                continue
            m = m.groupdict()

            if isinstance(ret, dict):
                key = m.pop(group_by)
                ret[key] = m
            else:
                ret.append(m)
        return ret

def cmd_parse(command, parser):
    return parser(command())

def zdb_datasets(*args):
    return cmd_parse(
        ZdbCommand('-d', *args),
        RegexParser(r'^Dataset (?P<group_by>[^ ]+) \[ZPL\], ID (?P<id>\d+), cr_txg (?P<cr_txg>\d+), (?P<size>[0-9\.]+\w), (?P<objects>\d+) objects$',
                    skip=1,
                    strict=True)
        )

def zpool_status(pool):
    if not pool:
        raise Exception("Cannot get status of pool '%s'", pool)
    z = ZPoolCommand('status')
    data = z(pool).splitlines()

    pool_re = re.match(r'^\s+pool:\s+(\w+)', data[0])
    if not pool_re:
        raise Exception("Could not find pool name in response: '%s'")
    pool = pool_re.group(0)

    parser = RegexParser('^\t +(?P<group_by>\w+\d+)\s+(?P<state>\w+)\s+(?P<read>\d+)\s+(?P<write>\d+)\s+(?P<cksum>\d+)$',
                         strict=True)

    return parser(*data[7:])

