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

## TODO Fixtures for default network config
class NetworkInterfaceConfig(model.Models):
    name = models.CharField(max_length=32)
    ipaddr = models.IPAddressField()
    netmask = models.CharField()
    gateway = models.IPAddressField()
    proto = models.CharField(max_length=32)
    #type = models.CharField(max_length=32)
    mtu = models.IntegerField(null=True)
    ## TODO Is JSONField best for DNS information? Easy I suppose..
    dns = JSONField()
