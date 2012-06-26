from django.db import models

import datetime


from numarray import *

from django.utils import timezone

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

#class Config(models.Model):
#    key = models.CharField(max_length=255)
#    value = models.CharField(max_length=255)
#    def __unicode__(self):
#        return self.key

