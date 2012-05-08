#!/usr/bin/env python

import os, sys
import time, datetime, logging
from django.utils import timezone
from iterpipes import run, cmd, linecmd, check_call, format
from solarsanweb.utils import FilterableDict
from solarsanweb.solarsan.utils import convert_bytes_to_human, convert_human_to_bytes

paths = {'zfs':    "/usr/sbin/zfs",
         'zpool':  "/usr/sbin/zpool", }

def _zfscmd(cmd, *args):
    """ Returns a linecmd with auto args """
    cmdf = []
    for i in range(len(args)):
        cmdf.append('{}')
    cmdf = ' '.join(cmdf)
    logging.debug("_zfscmd: %s %s", cmd, args)
    return linecmd(paths[cmd]+' '+cmdf, *args)

def zpool(*args):
    return _zfscmd('zpool', *args)
    """ Returns linecmd for zfs execution """

def zfs(*args):
    return _zfscmd('zfs', *args)
    """ Returns linecmd for zfs execution """

def zpool_list(*pools, **kwargs):
    """ Utility to get a list of zfs pools and associated properties.
    Also aggregates parent/children information """

    args = ['list', '-H']
    if kwargs.get('recursive', False) == True:
        args.append('-r')
    props = kwargs.get('props', ['name','allocated','capacity','dedupratio','free','guid','health',
                                 'size','altroot','ashift','autoexpand','autoreplace','bootfs',
                                 'cachefile','dedupditto','delegation','failmode','listsnapshots',
                                 'readonly','version'] )
    args.extend([ '-o', ','.join(props) ])
    if pools:
        if len(pools) == 1:
            pools = [pools]
        args.extend(*pools)

    pool_list = {}
    for line in run(zpool(*args)):
        line = str(line).rstrip("\n").split("\t")
        # Wooooooh
        pool = dict(zip(props, line))
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

def zpool_iostat(*pools, **kwargs):
    """ Utility to return zpool iostats on the specified pools """
    args = ['iostat', '-Tu']
    if pools:
        if len(pools) == 1:
            pools = [pools]
        args.extend(*pools)
    capture_length = str(kwargs.get('capture_length', '30'))
    how_many = str(int(kwargs.get('how_many', 1)) + 1)
    args.extend([capture_length, how_many])

    iostat = {}
    timestamp = False
    skip_past_dashline = False
    for line in run(zpool(*args)):
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
            raise Exception

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
            raise Exception
    return iostat

def zfs_destroy(name, **kwargs):
    """ [DANGEROUS] Delete dataset from filesystem """
    args = ['destroy']
    if kwargs.get('recursive', False) == True:
        args.append('-r')
    if not name:
        logging.error("zfs_destroy was attemped with an empty name")
        raise Exception
    if name.contains('@'):
        type = 'snapshot'
    else:
        type = 'filesystem'
        #type = 'dataset'
    args.append(name)

    logging.info('Destroying %s %s', type, name)
    return check_call(zfs(*args))

def zfs_snapshot(name, **kwargs):
    """ Create snapshot """
    args = ['snapshot']
    if kwargs('recursive', False) == True:
        args.append('-r')
    #if kwargs.get('name_strftime', True) == True:
    #    name = timezone.now().strftime(name)
    if not name:
        logging.error("zfs_snapshot was attempted with an empty name")
        raise Exception
    if not name.contains('@'):
        logging.error("zfs_snapshot was attempted with an invalid snapshot name (missing @): %s", name)
        raise Exception
    args.append(name)

    logging.info('Creating snapshot %s with %s', name, kwargs)
    return check_call(zfs(*args))

def zfs_list(*names, **kwargs):
    """ Utility to get a list of zfs volumes and associated properties.
    Also aggregates parent/children information """
    args = ['list', '-H', '-t', kwargs.get('type', 'all')]
    if 'depth' in kwargs:
        args.extend([ '-d', kwargs['depth'] ])
    if kwargs('recursive', False) == True:
        args.append('-r')
    props = kwargs.get('props', ['name', 'type', 'used', 'available', 'creation', 'referenced',
                                 'compressratio', 'mounted', 'quota', 'reservation', 'recordsize',
                                 'mountpoint', 'sharenfs', 'checksum', 'compression', 'atime',
                                 'devices', 'exec', 'setuid', 'readonly', 'zoned', 'snapdir',
                                 'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only',
                                 'normalization', 'casesensitivity', 'vscan', 'nbmand', 'sharesmb',
                                 'refquota', 'refreservation', 'primarycache', 'secondarycache',
                                 'usedbysnapshots', 'usedbydataset', 'usedbychildren',
                                 'usedbyrefreservation', 'logbias', 'dedup', 'mlslabel', 'sync',
                                 'refcompressratio'] )
    args.extend([ '-o', ','.join(props) ])
    if names:
        args.extend(*names)

    # Run command and parse output
    dataset_list = {}
    for line in run(zfs(*args)):
        line = str(line).rstrip("\n").split("\t")
        # Can't use bareword 'exec' like this, so Case it
        if 'exec' in props:
            props[ props.index('exec') ] = "Exec"
        # Wooooooh
        dataset = dict(zip(props, line))

        # Make some changes
        for key in dataset.iteritems():
            # Booleanize
            if key in ['mounted', 'defer_destroy', 'atime', 'devices', 'exec', 'nbmand', 'readonly',
                        'setuid', 'shareiscsi', 'vscan', 'xattr', 'zoned', 'utf8only' ]:
                if dataset[key] == "yes" or dataset[key] == "on":
                    dataset[key] = True
                elif dataset[key] == "no" or dataset[key] == "off" or dataset[key] == "-":
                    dataset[key] = False
            # Nullize
            elif dataset[key] == '-':
                if key in ['copies', 'version']:
                    dataset[key] = 0
                else:
                    dataset[key] = ''
        dataset_list[ dataset['name'] ] = dataset

    dataset_tree = {}
    # Generate parent <> child relationships and some extras like basename
    for d in dataset_list:
        d = dataset_list[d]

        # Add to dataset_tree
        path = os.path.split(d['name'])
        current_level = dataset_tree
        for part in path:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    # Send final output
    return dataset_list


