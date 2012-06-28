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
    key = models.CharField( max_length=255 )
    value = JSONField()
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

## TODO Fixtures for default network config
class NetworkInterfaceConfig( models.Model ):
    name = models.CharField( max_length=13, unique=True )
    ipaddr = models.IPAddressField()
    cidr = models.PositiveIntegerField( max_length=2 )                   # TODO Validate min=1 max=32
    proto = models.CharField( max_length=16, default='none' )            # static|dhcp|none
    mtu = models.PositiveIntegerField( default=1500 )

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
                'search': 'solarsan.local', }

    def __unicode__( self ):
        if self.ipaddr and self.cidr: return '%s (%s/%s)' % ( self.name, self.ipaddr, self.cidr )
        else: return self.name

class NetworkInterface( object ):
    def __init__( self, name ):
        self.name = name

        ## Get config for NIC if it exists, otherwise new instance; don't save it to DB at this point.
        try:
            self.config = NetworkInterfaceConfig.objects.get( name=name )
        except ( NetworkInterfaceConfig.DoesNotExist ):
            self.config = NetworkInterfaceConfig( name=name )

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




