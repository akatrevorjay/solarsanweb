#!/usr/bin/env python

import os, sys
import time, datetime, logging, dateutil
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
    """ Returns linecmd for zfs execution """
    return _zfscmd('zpool', *args)


def zfs(*args):
    """ Returns linecmd for zfs execution """
    return _zfscmd('zfs', *args)


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
        args.extend(pools)

    pool_list = FilterableDict()
    for line in run(zpool(*args)):
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


def zpool_iostat(*pools, **kwargs):
    """ Utility to return zpool iostats on the specified pools """
    args = ['iostat', '-Tu']
    if pools:
        args.extend(pools)
    capture_length = str(kwargs.get('capture_length', '30'))
    how_many = str(int(kwargs.get('how_many', 1)) + 1)
    args.extend([capture_length, how_many])

    iostat = FilterableDict()
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


## zfs possible outcomes for datasets
#volblocksize === blocksize
#aclinherit === discard | noallow | restricted | passthrough | passthrough-x
#aclmode === discard | groupmask | passthrough
#atime === on | off
#canmount === on | off | noauto
#checksum === on | off | fletcher2,| fletcher4 | sha256
#compression === on | off | lzjb | gzip | gzip-N
#copies === 1 | 2 | 3
#devices === on | off
#exec === on | off
#mountpoint === path | none | legacy
#nbmand === on | off
#primarycache === all | none | metadata
#quota === size | none
#readonly === on | off
#recordsize === size
#refquota === size | none
#refreservation === size | none
#reservation === size | none
#secondarycache === all | none | metadata
#setuid === on | off
#shareiscsi === on | off
#sharesmb === on | off | opts
#sharenfs === on | off | opts
#snapdir === hidden | visible
#version === 1 | 2 | current
#volsize === size
#vscan === on | off
#xattr === on | off
#zoned === on | off
#casesensitivity === sensitive | insensitive | mixed

def zfs_list(*names, **kwargs):
    """ Utility to get a list of zfs volumes and associated properties.
    Also aggregates parent/children information """
    args = ['list', '-H', '-t', kwargs.get('type', 'all')]
    if 'depth' in kwargs:
        args.extend([ '-d', kwargs['depth'] ])
    if kwargs.get('recursive', False) == True:
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
        args.extend(names)

    # Run command and parse output
    dataset_list = FilterableDict()
    for line in run(zfs(*args)):
        line = str(line).rstrip("\n").split("\t")
        # Can't use bareword 'exec' like this, so Case it
        if 'exec' in props:
            props[ props.index('exec') ] = "Exec"
        # Wooooooh
        dataset = dict(zip(props, line))

        # Make some changes
        for key, val in dataset.iteritems():
            # Booleanize
            if key in ['mounted', 'defer_destroy', 'atime', 'devices', 'exec', 'nbmand', 'readonly',
                        'setuid', 'shareiscsi', 'vscan', 'xattr', 'zoned', 'utf8only' ]:
                if val in ['yes', 'on']:
                    dataset[key] = True
                elif val in ['no', 'off', '-']:
                    dataset[key] = False
            # Nullize
            elif dataset[key] == '-':
                if key in ['copies', 'version']:
                    dataset[key] = 0
                else:
                    dataset[key] = ''
            # Datetimeize
            if key in ['creation']:
                # TZify the timestamp
                dataset[key] = timezone.make_aware(
                        dateutil.parser.parse(val), timezone.get_current_timezone() )
        dataset_list[ dataset['name'] ] = dataset

    # Send final output
    return dataset_list


def tree():
    """ Generate nice dict of parsed ZFS pools/datasets in a tree showing parent/child relationship """
    pools = zpool_list()
    datasets = zfs_list()
    tree = FilterableDict()

    # Add pools
    tree = dict(( (pk, {'pool': pv}) for pk, pv in pools.iteritems() ))

    # Add datasets
    for dk,dv in datasets.iteritems():
        path = dk.split(os.path.sep)
        if dv['type'] == 'snapshot':
            (path[len(path) - 1], snapshot_name)  = path[len(path) - 1].rsplit('@', 1)

        current_level = tree
        for part in path:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

        if dv['type'] == 'snapshot':
            if 'snapshots' not in current_level:
                current_level['snapshots'] = {}
            current_level['snapshots'][ snapshot_name ] = dv
            current_level = current_level['snapshots']
        else:
            current_level[ '-'+dv['type'] ] = dv

    return tree

class tree_obj(FilterableDict):
    """ Generate nice dict of parsed ZFS pools/datasets in a tree showing parent/child relationship """
    lock_timeout = 60
    locked = False
    def __init__(self, *args, **kwargs):
        super(tree_obj, self).__init__(self, *args, **kwargs)
        self.refresh()
    def check_if_locked(self):
        """ Checks if we're locked and if so, waits until self.lock_timeout (default: 60) seconds before giving up """
        if self.locked == True:
                count = 0
                while self.locked == True:
                    time.sleep(1)
                    count+=1
                    if count > self.lock_timeout / 2:
                        logging.warning("Halfway to timeout while waiting for lock to be released [timeout=%s]",
                                self.lock_timeout)
                    if count > self.lock_timeout:
                        raise Exception('Timed out while waiting for lock to be released [timeout=%s]'
                                % self.lock_timeout)
    def __getitem__(self, arg):
        """ Wrapper to check locks """
        self.check_if_locked()
        return super(tree_obj, self).__getitem__(arg)
    def __setitem__(self, *args, **kwargs):
        """ Wrapper to check locks """
        self.check_if_locked()
        return super(tree_obj, self).__setitem__(self, *args, **kwargs)
    def refresh(self):
        """ Generate nice dict of parsed ZFS pools/datasets in a tree showing parent/child relationship """
        # Get new tree
        try:
            pools = zpool_list()
            datasets = zfs_list()
        except:
            raise Exception("zfs.refresh: Could not get new data")

        def add_objects_to_tree(*args):
            """ Adds *args to tree; ets reused for any kind of object being added """
            for arg in args:
                for key,value in arg.iteritems():
                    path = key.split(os.path.sep)
                    # If this is a snapshot, split the snapshot name from the filesytem name
                    if value['type'] == 'snapshot':
                        path.extend(path.pop().rsplit('@', 1))
                    # Go to base of tree
                    current_level = tree
                    # Snag name
                    name = path.pop()
                    # Move down the ladder
                    for part in path:
                        if part not in current_level:
                            current_level[part] = FilterableDict()
                        current_level = current_level[part]
                    # Apply dataset contents to pluralized dataset type, ie .snapshots
                    try:
                        typelist = getattr(current_level, value['type']+'s')
                    except (AttributeError):
                        typelist = FilterableDict()
                    typelist[name] = value
                    setattr(current_level, value['type']+'s', typelist)
                    # Set .has attribute
                    try:
                        has = getattr(current_level, 'has')
                    except (AttributeError):
                        has = []
                    if value['type']+'s' not in has:
                        has.append(value['type']+'s')
                        setattr(current_level, 'has', has)

        # Start tree, add pools
        tree = FilterableDict()
        add_objects_to_tree(pools, datasets)

        # Do a locked update
        try:
            self.check_if_locked()
            self.locked = True
            self.clear()
            self.update(tree)
            # hack
            setattr(self, 'has', getattr(tree, 'has'))
            for has in self.has:
                setattr(self, has, getattr(tree, has))
            self.locked = False
        except:
            raise Exception("Could not do a locked update")
        finally:
            self.locked = False

#def parse_zfs_date(date):
#    time_format = "%a %b %d %H:%M %Y"
#    dataset['creation'] = timezone.make_aware(
#            datetime.datetime.fromtimestamp(
#                time.mktime(
#                    time.strptime(dataset['creation'],
#                    time_format )))


