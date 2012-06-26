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

class ClusterNode( models.Model ):
    """ Recently seen peers """
    ip = models.IPAddressField( unique=True )
    #enabled = models.BooleanField( default=False )
    last_seen = models.DateTimeField( auto_now=True )
    #first_seen = models.DateTimeField()
    #objects = EnabledModelManager()
    #objects_all = models.Manager()

"""
Network
"""

class iface(model.Models):
    name = models.CharField('max_length=12')
    ip = models.IPAddressField()
    mtu = models.IntegerField()
    netmask = models.IPAddressField()
    proto = models.CharField('max_length=10')
    type = models.CharField('max_length=12')
    gateway = models.IPAddressField()

class dns(models.Models):
    search = models.IPAddressField()
    server = []
    iface = models.ForeignKey(iface)

