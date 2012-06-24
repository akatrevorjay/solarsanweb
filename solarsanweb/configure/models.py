from solarsan.models import EnabledModelManager
from jsonfield import JSONField
from django.db import models
import logging


class Config( models.Model ):
    """ Simple Key<=>JSON store for config entries """
    key = models.CharField( max_length=255 )
    value = JSONField()
    def __unicode__( self ):
        return self.key + '=' + self.value


class ClusterNode( models.Model ):
    """ Recently seen peers """
    ip = models.IPAddressField( unique=True )
    #enabled = models.BooleanField( default=False )
    last_seen = models.DateTimeField( auto_now=True )
    #first_seen = models.DateTimeField()
    #objects = EnabledModelManager()
    #objects_all = models.Manager()



