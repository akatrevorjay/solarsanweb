"""
$ zfs/dataset.py -- Interface to zfs command line utilities
~ Trevor Joynson (trevorj) <trevorj@localhostsolutions.com>
"""

import logging, dateutil
from django.utils import timezone
from solarsan.utils import FilterableDict
import cmd


"""
Dataset Handling
"""

def destroy( name, **kwargs ):
    """ [DANGEROUS] Delete dataset from filesystem """
    zargs = ['destroy']
    if kwargs.get( 'recursive', False ) == True:
        zargs.append( '-r' )
    if not name:
        raise Exception( "destroy was attemped with an empty name" )
    if '@' in name:
        type = 'snapshot'
    else:
        type = 'filesystem'
        #type = 'dataset'
    zargs.append( name )

    logging.info( 'Destroying %s %s', type, name )
    cmd.zfs(*zargs, error=True)
    try:
        list( name )
    except:
        return True
    raise Exception( "ZFS destroy of '%s' was successful, but the destroyed dataset still exists?" % name )

def create( name, **kwargs ):
    """ Create filesystem """
    zargs = ['create']
    # TODO -o opts
    if not name:
        raise Exception( "filesystem was attempted with an empty name" )
    zargs.append( name )

    logging.info( 'Creating snapshot %s with %s', name, kwargs )
    cmd.zfs(*zargs, error=True)
    return list( name )

def snapshot( name, **kwargs ):
    """ Create snapshot """
    zargs = ['snapshot']
    if kwargs.get( 'recursive', False ) == True:
        zargs.append( '-r' )
    #if kwargs.get('name_strftime', True) == True:
    #    name = timezone.now().strftime(name)
    if not name:
        raise Exception( "snapshot was attempted with an empty name" )
    if not '@' in name:
        raise Exception( "snapshot was attempted with an invalid snapshot name (missing @): %s" % name )
    zargs.append( name )

    logging.info( 'Creating snapshot %s with %s', name, kwargs )
    cmd.zfs(*zargs, error=True)
    return list( name )

""" zfs possible outcomes for datasets
 volblocksize === blocksize
 aclinherit === discard | noallow | restricted | passthrough | passthrough-x
 aclmode === discard | groupmask | passthrough
 atime === on | off
 canmount === on | off | noauto
 checksum === on | off | fletcher2,| fletcher4 | sha256
 compression === on | off | lzjb | gzip | gzip-N
 copies === 1 | 2 | 3
 devices === on | off
 exec === on | off
 mountpoint === path | none | legacy
 nbmand === on | off
 primarycache === all | none | metadata
 quota === size | none
 readonly === on | off
 recordsize === size
 refquota === size | none
 refreservation === size | none
 reservation === size | none
 secondarycache === all | none | metadata
 setuid === on | off
 shareiscsi === on | off
 sharesmb === on | off | opts
 sharenfs === on | off | opts
 snapdir === hidden | visible
 version === 1 | 2 | current
 volsize === size
 vscan === on | off
 xattr === on | off
 zoned === on | off
 casesensitivity === sensitive | insensitive | mixed
"""

def list( *names, **kwargs ):
    """ Utility to get a list of zfs volumes and associated properties.
        Also aggregates parent/children information """
    zargs = ['list', '-H', '-t', kwargs.get( 'type', 'all' )]
    if 'depth' in kwargs:
        zargs.extend( [ '-d', str(kwargs['depth']) ] )
    if kwargs.get( 'recursive', False ) == True:
        zargs.append( '-r' )
    props = kwargs.get( 'props', ['name', 'type', 'used', 'available', 'creation', 'referenced',
                                 'compressratio', 'mounted', 'quota', 'reservation', 'recordsize',
                                 'mountpoint', 'sharenfs', 'checksum', 'compression', 'atime',
                                 'devices', 'exec', 'setuid', 'readonly', 'zoned', 'snapdir',
                                 'aclinherit', 'canmount', 'xattr', 'copies', 'version', 'utf8only',
                                 'normalization', 'casesensitivity', 'vscan', 'nbmand', 'sharesmb',
                                 'refquota', 'refreservation', 'primarycache', 'secondarycache',
                                 'usedbysnapshots', 'usedbydataset', 'usedbychildren',
                                 'usedbyrefreservation', 'logbias', 'dedup', 'mlslabel', 'sync',
                                 'refcompressratio'] )
    if isinstance(props, basestring): props = [props]
    if isinstance(props, tuple): props = list(props)
    if 'name' not in props: props.append('name')

    zargs.extend( [ '-o', ','.join(props).lower() ] )
    if names:   zargs.extend( names )

    # Hide stderr if requested, or merge with stdout, etc
    if kwargs.get( 'stderr', None ) == 'stdout':  zargs.append( '2>&1' )
    else:                                       zargs.append( '2>/dev/null' )

    # Can't use bareword 'exec' like this, so Case it
    if 'exec' in props:
        props[ props.index( 'exec' ) ] = "Exec"

    # Run command and parse output
    dataset_list = {}
    for line in cmd.zfs(*zargs).splitlines():
        line = line.rstrip("\n")
        line = dict( zip( props, str( line ).split( "\t" ) ) )

        # Make some changes
        # WTF Did I do this and not just keep em as varchars?
        for key, val in line.items():
            # Booleanize
            if key in ['mounted', 'defer_destroy', 'atime', 'devices', 'exec', 'nbmand', 'readonly',
                        'setuid', 'shareiscsi', 'vscan', 'xattr', 'zoned', 'utf8only', 'dedup' ]:
                if val in ['yes', 'on']:
                    line[key] = True
                elif val in ['no', 'off', '-']:
                    line[key] = False
            # Nullize
            elif line[key] == '-':
                if key in ['copies', 'version']:
                    line[key] = 0
                else:
                    line[key] = ''
            # Datetimeize
            elif key in ['creation']:
                # TZify the timestamp
                line[key] = timezone.make_aware(
                        dateutil.parser.parse( val ), timezone.get_current_timezone() )

        dataset_list[ line['name'] ] = line
    # Send final output
    return dataset_list

"""
Dataset Properties
"""

def get( datasets, *args, **kwargs ):
    """ Gets properties on *datasets """
    zargs = ['get', '-Hp']
    if not datasets:            raise Exception( "Get: No datasets were given?" )
    if not args:                raise Exception( "Get: No props were given?" )

    if 'depth' in kwargs:       zargs.extend( [ '-d', kwargs['depth'] ] )
    if 'source' in kwargs:      zargs.extend( [ '-s', kwargs['source'] ] )
    if kwargs.get( 'recursive', False ) == True:
        zargs.append( '-r' )

    # Append each property.
    zargs.extend( [ (','.join(args)) ] )
    # Datasets get tacked on last.
    zargs.extend( [ ( dataset ) for dataset in datasets ] )

    logging.info( "Getting properties '%s' on dataset '%s': with %s", ', '.join(args), dataset, kwargs )
    cmd.zfs(*zargs, error=True)
    return list( dataset )


def set( dataset, **kwargs ):
    """ Sets properties on dataset """
    zargs = ['set']

    if not dataset:
        raise Exception( "set was attempted with an empty name" )
    if not len( kwargs.keys() ) > 0:
        raise Exception( "set was attempted with an empty prop list" )
    # Append each property
    for k, v in kwargs.iteritems():
        zargs.append( k + '=' + v )
    zargs.append( dataset )

    logging.info( "Setting properties on dataset '%s': with %s", dataset, kwargs )
    cmd.zfs(*zargs, error=True)
    return list( dataset )
