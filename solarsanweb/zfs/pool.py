""""
$ zfs/cmd.py -- Interface to zfs command line utilities
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

#import os, sys
import datetime, logging
from django.utils import timezone
import iterpipes
from solarsan.utils import FilterableDict, convert_human_to_bytes
from .common import Error, NotImplemented

import cmd

"""
Pool Handling
"""

#create [-fn] [-o property=value] ...
#     [-O file-system-property=value] ...
#     [-m mountpoint] [-R root] <pool> <vdev> ...

def create(name, **kwargs):
    """ Create pool """
    # TODO HDD selector in web gui that lets you build pools
    #   No need to support anything but RAID10
    raise NotImplemented

    zargs = ['create']
    # TODO -o opts; compress=on, atime=off, etc
    if not name:
        raise Error("zfs_pool was attempted with an empty name")
    zargs.append(name)

    logging.info('Creating pool %s with %s', name, kwargs)
    iterpipes.check_call(cmd.zpool(*zargs))
    return list(name)

def destroy():
    raise NotImplemented

def add():
    raise NotImplemented

def remove():
    raise NotImplemented


def list(*pools, **kwargs):
    """ Utility to get a list of zfs pools and associated properties.
    Also aggregates parent/children information """

    zargs = ['list', '-H']
    if kwargs.get('recursive', False) == True:
        zargs.append('-r')
    props = kwargs.get('props', ['name','allocated','capacity','dedupratio','free','guid','health',
                                 'size','altroot','ashift','autoexpand','autoreplace','bootfs',
                                 'cachefile','dedupditto','delegation','failmode','listsnapshots',
                                 'readonly','version'] )
    if isinstance(props, basestring): props = [props]
    if isinstance(props, tuple): props = list(props)
    if 'name' not in props: props.append('name')

    zargs.extend([ '-o', ','.join(props).lower() ])
    if pools:
        zargs.extend(pools)

    # Hide stderr if requested, or merge with stdout, etc
    stderr = kwargs.get('stderr', None)
    if stderr == 'stdout':
        zargs.append('2>&1')
    elif stderr == None:
        zargs.append('2>/dev/null')


    pool_list = FilterableDict()
    for line in iterpipes.run(cmd.zpool(*zargs)):
        line = str(line).rstrip("\n").split("\t")
        # Wooooooh
        pool = dict(zip(props, line))
        pool['type'] = 'pool'
        # Make some changes
        for key in pool.iterkeys():
            # Booleanize
            if key in ['autoexpand', 'autoreplace', 'delegation', 'listsnapshots', 'readonly']:
                if pool[key] == "yes" or pool[key] == "on":
                    pool[key] = True
                elif pool[key] == "no" or pool[key] == "off" or pool[key] == "-":
                    pool[key] = False
            # Nullize
            elif pool[key] == '-':
                if key in ['copies', 'version']:
                    pool[key] = 0
                else:
                    pool[key] = ''
        pool_list[ pool['name'] ] = pool
    return pool_list


def iostat(*pools, **kwargs):
    """ Utility to return zpool iostats on the specified pools """
    zargs = ['iostat', '-Tu']
    if pools:
        zargs.extend(pools)
    capture_length = str(kwargs.get('capture_length', '30'))
    how_many = str(int(kwargs.get('how_many', 1)) + 1)
    zargs.extend([capture_length, how_many])

    iostat = FilterableDict()
    timestamp = False
    skip_past_dashline = False
    for line in iterpipes.run(cmd.zpool(*zargs)):
        line = str(line).rstrip("\n")

        # Got a timestamp
        if line.isdigit():
            # If this is our first record, skip till we get the header seperator
            if not timestamp:
                skip_past_dashline = True
            # TZify the timestamp
            timestamp = timezone.make_aware(
                    datetime.datetime.fromtimestamp(int(line)), timezone.get_current_timezone() )
            continue

        # If we haven't gotten the dashline yet, wait till the line after it
        if skip_past_dashline == True:
            if line.startswith('-----'):
                skip_past_dashline = False
            continue

        # If somehow we got here without a timestamp, something is probably wrong.
        if timestamp == False:
            logging.error("Got unexpected input from zpool iostat: %s", line)
            raise Error

        try:
            # Parse iostats output
            j = {}
            (name, j['alloc'], j['free'], j['iops_read'], j['iops_write'], j['bandwidth_read'],
                    j['bandwidth_write']) = line.split()
            j = dict( [(key, convert_human_to_bytes(value)) for key, value in j.iteritems() ])
            (j['name'], j['timestamp']) = (name, timestamp)
            iostat[j['name']] = j
        except:
            logging.error("Could not parse input from zpool iostat: %s", line)
            raise Error
    return iostat


def status():
    raise NotImplemented

def offline():
    raise NotImplemented

def clear():
    raise NotImplemented

def attach():
    raise NotImplemented

def detach():
    raise NotImplemented

def replace():
    raise NotImplemented

def splite():
    raise NotImplemented

def scrub():
    raise NotImplemented

def Import():
    raise NotImplemented

def export():
    raise NotImplemented

def upgrade():
    raise NotImplemented

def history():
    raise NotImplemented

def events():
    raise NotImplemented




