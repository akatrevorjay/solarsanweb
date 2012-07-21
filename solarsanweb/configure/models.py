#from solarsan.models import EnabledModelManager
#from jsonfield import JSONField
from django.db import models
from django.utils import timezone
import datetime
#import logging

from django_mongokit import connection
from django_mongokit.document import DjangoDocument

"""
Config
"""

@connection.register
class ConfigEntry(DjangoDocument):
    class Meta:
        verbose_name_plural = 'Configuration Entries'
    collection_name = 'config'
    use_dot_notation = True

    structure = {
        'key': unicode,
        'val': None,
        'last_modified': datetime.datetime,
        'created': datetime.datetime,
    }

    required_fields = ['key']

    default_values = {
        'last_modified': timezone.now,
        'created': timezone.now,
    }

    indexes = [
        {'fields': ['key'], 'unique': True},
    ]


"""
Cluster
"""

import re

class MinLengthValidator(object):
    def __init__(self, min_length):
        self.min_length = min_length
    def __call__(self, value):
        if not len(value) >= self.min_length:
            raise Exception('%s must be at least ' + str(self.min_length) + ' characters long.')

import ipcalc, IPy

class IPAddressValidator(object):
    def __init__(self, *args, **kwargs):
        self.req = kwargs.get('require', kwargs.get('req', []))
        self.req.extend(args)
    def __call__(self, value):
        try:
            #ip = IPy.IP(value)
            ip = ipcalc.Network(value)
        except (ValueError):
            raise Exception('%s must be a valid IP address')
        for x in ['IPv4', 'IPv6']:
            #if x.lower in self.req and ip.version != int(x[-1]):
            if x.lower in self.req and ip.version() != int(x[-1]):
                raise Exception('%%s must be a valid %s address' % x)

class RegexValidator(object):
    def __init__(self, pattern, opts=None, name='match'):
        if not hasattr(self, 'regex'):
            self.regex = re.compile(pattern, opts)
        if not hasattr(self, 'name'):
            self.name = name
    def __call__(self, value):
        if not bool(self.regex.match(value)):
            raise Exception('%s' + 'is not a valid %s (%s)' % (self.name, self.regex.pattern))

class EmailValidator(RegexValidator):
    name = 'email'
    regex = re.compile(r'(?:^|\s)[-a-z0-9_.]+@(?:[-a-z0-9]+\.)+[a-z]{2,6}(?:\s|$)', re.IGNORECASE)


@connection.register
class ClusterNode(DjangoDocument):
    class Meta:
        verbose_name_plural = 'ClusterNodes'
    collection_name = 'cluster_nodes'
    use_dot_notation = True

    structure = {
        'hostname': unicode,
        #'uuid': unicode, #uuid.UUID
        'interfaces': {
            unicode: {                                  # name
                unicode: [ (unicode, unicode), ],        # af [ (addr,netmask), ]
            },
        },
        'last_seen': datetime.datetime,
        'first_seen': datetime.datetime,
    }

    required_fields = ['hostname',]

    default_values = {
        'last_seen': timezone.now,
        'first_seen': timezone.now,
    }

    validators = {
        #'hostname': RegexValidator(r'^[a-z0-9]+$', re.IGNORECASE),
    }

    def validate(self, *args, **kwargs):
        v_iface_name = re.compile(r'^((eth|ib)\d{1,2}|lo)$', re.IGNORECASE)
        v_afs = netifaces.address_families.values()
        for iface_name,iface in self['interfaces'].iteritems():
            assert bool(v_iface_name.match(iface_name))
            for af, addrs in iface.iteritems():
                assert af in v_afs
                for ip,mask in addrs:
                    #try:
                    ip = ipcalc.Network( "%s/%s" % (ip, mask) )
                    #except:
                    #    addrs.remove([ip,mask])
                    #    #assert False
        super(ClusterNode, self).validate(*args, **kwargs)

    indexes = [
        {'fields': ['hostname'], 'unique': True},
        #{'fields': ['uuid'], 'unique': True},
    ]

#connection.register([ClusterNode])


"""
Network
"""
import netifaces
#from django.core.urlresolvers import reverse

def convert_cidr_to_netmask(arg):
    return str( IPy.IP('0/%s' % arg, make_net=True).netmask() )

def convert_netmask_to_cidr(arg):
    return int( IPy.IP('0/%s' % arg, make_net=True).prefixlen() )

## TODO Fixtures for default network config
class NetworkInterfaceConfig( models.Model ):
    PROTO_CHOICES = ( 
        ( 'none', 'Disabled' ),
        ( 'static', 'Static IP' ),
        ( 'dhcp', 'DHCP' ),
    )
    ## TODO Add 8-32
    CIDR_CHOICES = ( 
        ( 1, '128.0.0.0' ),
        ( 2, '192.0.0.0' ),
        ( 3, '224.0.0.0' ),
        ( 4, '240.0.0.0' ),
        ( 5, '248.0.0.0' ),
        ( 6, '252.0.0.0' ),
        ( 7, '254.0.0.0' ),
        ( 8, '255.0.0.0' ),
        ( 9, '255.128.0.0' ),
        ( 10, '255.192.0.0' ),
        ( 11, '255.224.0.0' ),
        ( 12, '255.240.0.0' ),
        ( 13, '255.248.0.0' ),
        ( 14, '255.252.0.0' ),
        ( 15, '255.254.0.0' ),
        ( 16, '255.255.0.0' ),
        ( 17, '255.255.128.0' ),
        ( 18, '255.255.192.0' ),
        ( 19, '255.255.224.0' ),
        ( 20, '255.255.240.0' ),
        ( 21, '255.255.248.0' ),
        ( 22, '255.255.252.0' ),
        ( 23, '255.255.254.0' ),
        ( 24, '255.255.255.0' ),
        ( 25, '255.255.255.128' ),
        ( 26, '255.255.255.192' ),
        ( 27, '255.255.255.224' ),
        ( 28, '255.255.255.240' ),
        ( 29, '255.255.255.248' ),
        ( 30, '255.255.255.252' ),
        ( 31, '255.255.255.254' ),
        ( 32, '255.255.255.255' ),
    )
    #NETMASK_CHOICES = dict(zip(CIDR_CHOICES.values(), CIDR_CHOICES.keys())

    name = models.CharField( max_length=13, unique=True )
    ipaddr = models.IPAddressField( verbose_name='IP Address' )
    cidr = models.PositiveIntegerField( max_length=2, choices=CIDR_CHOICES, verbose_name='Netmask' )
    proto = models.CharField( max_length=16, default='none', choices=PROTO_CHOICES, verbose_name='Protocol' )
    mtu = models.PositiveIntegerField( default=1500, verbose_name='MTU' )
    last_modified = models.DateTimeField( auto_now=True )
    created = models.DateTimeField( auto_now_add=True )

    @property
    def netmask( self ):
        return str( ipcalc.Network( '1.1.1.1/%s' % self.cidr ).netmask() )

    ## TODO This should probably be a global Config() entry instead of hard-coded crap or being per-interface
    #gateway = models.IPAddressField()
    @property
    def gateway( self ):
        return '10.16.38.254'

    ## TODO This should probably be a global Config() entry instead of hard-coded crap or being per-interface
    #dns = JSONField()
    @property
    def dns( self ):
        return {'nameservers': ['8.8.8.8', '8.8.4.4'],
                'search': ['solarsan.local'], }

    #def get_absolute_url( self ):
    #    return reverse( 'network-interface-detail', kwargs={'slug': self.name} )

    def __unicode__( self ):
        if self.ipaddr and self.cidr: return '%s (%s/%s)' % ( self.name, self.ipaddr, self.cidr )
        else: return self.name


class NetworkInterface( object ):
    def __init__( self, name ):
        #if not name in netifaces.interfaces():
            #raise Exception( 'No interface found with name %s' % name )
        self.name = name

        ## Get config for NIC if it exists, otherwise new instance; don't save it to DB at this point.
        try:
            self.config = NetworkInterfaceConfig.objects.get( name=name )
        #except ( NetworkInterfaceConfig.DoesNotExist ):
        except:
            ## Get starting config from the first AF_INET address on the device (if it exists)
            config = {'name': name}
            addrs = self.addrs
            if 'AF_INET' in addrs:
                addr = addrs['AF_INET'][0]
                config['ipaddr'] = addr['addr']
                config['cidr'] = int( ipcalc.Network( '1.1.1.1/%s' % addr['netmask'] ).mask )
            else:
                # If no IPs are on this interface, start with a /24 subnet mask
                config['cidr'] = 24
            self.config = NetworkInterfaceConfig( **config )

        ## TODO Populate DNS information
        self.dns = self.config.dns

    @property
    def addrs( self ):
        ret = dict( [( netifaces.address_families[x[0]], x[1] )
                       for x in netifaces.ifaddresses( self.name ).items() ] )
        if 'AF_INET6' in ret:
            ## TODO Fix bug in the real issue here, netifaces, where it puts your damn iface name after your IPv6 addr
            inet6_addrs = []
            for addr in ret['AF_INET6']:
                if '%' in addr['addr']:
                    addr['addr'] = addr['addr'][:addr['addr'].index('%')]
                inet6_addrs.append(addr)
            ret['AF_INET6'] = inet6_addrs
        return ret

    @property
    def type( self ):
        if   self.name.startswith( 'eth' ): return 'ethernet'
        elif self.name.startswith( 'ib' ):  return 'infiniband'
        elif self.name.startswith( 'lo' ):  return 'local'
        else:                               return None

    def __repr__( self ):
        return '<%s: %s>' % ( type( self ).__name__, self.name )


def NetworkInterfaceList():
    ret = {}
    for x in netifaces.interfaces():
        try:
            ret[x] = NetworkInterface(x)
        except:
            pass
    #return dict( [( x, lambda NetworkInterface( x ) except: None) for x in netifaces.interfaces()] )
    return ret

