from solarsan.models import EnabledModelManager
from jsonfield import JSONField
from django.db import models
from django.utils import timezone
import logging, datetime

"""
Config
"""

class Config( models.Model ):
    """ Simple Key<=>JSON store for config entries """
    key = models.CharField( max_length=255, unique=True )
    value = JSONField()
    last_modified = models.DateTimeField( auto_now=True )
    created = models.DateTimeField( auto_now_add=True )
    def __unicode__( self ):
        return self.key + '=' + self.value

"""
Cluster
"""

#class ClusterNode( models.Model ):
#    """ Recently seen peers """
#    ip = models.IPAddressField( unique=True )
#    #enabled = models.BooleanField( default=False )
#    last_seen = models.DateTimeField( auto_now=True )
#    #first_seen = models.DateTimeField()
#    #objects = EnabledModelManager()
#    #objects_all = models.Manager()

"""
Network
"""
import netifaces
import ipcalc
from django.core.urlresolvers import reverse


## TODO Fixtures for default network config
class NetworkInterfaceConfig( models.Model ):
    PROTO_CHOICES = ( 
        ( 'none', 'Disabled' ),
        ( 'static', 'Static IP' ),
        ( 'dhcp', 'DHCP' ),
    )
    ## TODO Add 8-32
    CIDR_CHOICES = ( 
        ( '8', '255.0.0.0' ),
        ( '16', '255.255.0.0' ),
        ( '24', '255.255.255.0' ),
        ( '29', '255.255.255.248' ),
    )
    #NETMASK_CHOICES = dict(zip(CIDR_CHOICES.values(), CIDR_CHOICES.keys())

    name = models.CharField( max_length=13, unique=True )
    ipaddr = models.IPAddressField()
    cidr = models.PositiveIntegerField( max_length=2, choices=CIDR_CHOICES )
    proto = models.CharField( max_length=16, default='none', choices=PROTO_CHOICES )
    mtu = models.PositiveIntegerField( default=1500 )
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

    def get_absolute_url( self ):
        return reverse( 'network-interface-detail', kwargs={'slug': self.name} )

    def __unicode__( self ):
        if self.ipaddr and self.cidr: return '%s (%s/%s)' % ( self.name, self.ipaddr, self.cidr )
        else: return self.name


class NetworkInterface( object ):
    def __init__( self, name ):
        if not name in netifaces.interfaces():
            raise Exception('No interface found with name %s' % name)
        self.name = name

        ## Get config for NIC if it exists, otherwise new instance; don't save it to DB at this point.
        try:
            self.config = NetworkInterfaceConfig.objects.get( name=name )
        except ( NetworkInterfaceConfig.DoesNotExist ):
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
        return dict( [( netifaces.address_families[x[0]], x[1] )
                      for x in netifaces.ifaddresses( self.name ).items() ] )

    @property
    def type( self ):
        if   self.name.startswith( 'eth' ): return 'ethernet'
        elif self.name.startswith( 'ib' ):  return 'infiniband'
        elif self.name.startswith( 'lo' ):  return 'local'
        else:                               return None

    def __repr__( self ):
        return '<%s: %s>' % ( type( self ).__name__, self.name )


def NetworkInterfaceList():
    return dict( [( x, NetworkInterface( x ) ) for x in netifaces.interfaces()] )




