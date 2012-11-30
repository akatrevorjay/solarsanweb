#from solarsan.models import EnabledModelManager
#from jsonfield import JSONField
from django.db import models
from django.utils import timezone
import datetime
#import logging

import mongoengine as m

import re
import ipcalc
import IPy
import netifaces
#from django.core.urlresolvers import reverse


"""
Cluster
"""


class ClusterNode(m.Document):
    meta = {'collection': 'cluster_nodes'}
    hostname = m.StringField(required=True, unique=True)
    # TODO Make this an embedded document
    interfaces = m.DictField()
    last_seen = m.DateTimeField()
    first_seen = m.DateTimeField()


"""
Network
"""


def convert_cidr_to_netmask(arg):
    return str(IPy.IP('0/%s' % arg, make_net=True).netmask())


def convert_netmask_to_cidr(arg):
    return int(IPy.IP('0/%s' % arg, make_net=True).prefixlen())


class NetworkInterface(m.Document):
    PROTO_CHOICES = (
        ('none', 'Disabled'),
        ('static', 'Static IP'),
        ('dhcp', 'DHCP'),
    )

    CIDR_CHOICES = (
        (1, '128.0.0.0'),
        (2, '192.0.0.0'),
        (3, '224.0.0.0'),
        (4, '240.0.0.0'),
        (5, '248.0.0.0'),
        (6, '252.0.0.0'),
        (7, '254.0.0.0'),
        (8, '255.0.0.0'),
        (9, '255.128.0.0'),
        (10, '255.192.0.0'),
        (11, '255.224.0.0'),
        (12, '255.240.0.0'),
        (13, '255.248.0.0'),
        (14, '255.252.0.0'),
        (15, '255.254.0.0'),
        (16, '255.255.0.0'),
        (17, '255.255.128.0'),
        (18, '255.255.192.0'),
        (19, '255.255.224.0'),
        (20, '255.255.240.0'),
        (21, '255.255.248.0'),
        (22, '255.255.252.0'),
        (23, '255.255.254.0'),
        (24, '255.255.255.0'),
        (25, '255.255.255.128'),
        (26, '255.255.255.192'),
        (27, '255.255.255.224'),
        (28, '255.255.255.240'),
        (29, '255.255.255.248'),
        (30, '255.255.255.252'),
        (31, '255.255.255.254'),
        (32, '255.255.255.255'),
    )

    #NETMASK_CHOICES = dict(zip(CIDR_CHOICES.values(), CIDR_CHOICES.keys()))

    name = m.StringField(unique=True)
    ipaddr = m.StringField()
    cidr = m.IntField()
    proto = m.StringField()
    mtu = m.IntField()
    modified = m.DateTimeField()
    created = m.DateTimeField()

    def __init__(self, name=None, **kwargs):
        if name:
            kwargs['name'] = name
        super(NetworkInterface, self).__init__(**kwargs)

        if not self.pk and self.name:
            # Get starting config from the first AF_INET address on the device (if it exists)
            addrs = self.addrs
            if 'AF_INET' in addrs:
                addr = addrs['AF_INET'][0]
                if not self.ipaddr:
                    self.ipaddr = addr['addr']
                if not self.cidr:
                    self.cidr = int(ipcalc.Network('1.1.1.1/%s' % addr['netmask']).mask)
                if not self.proto:
                    self.proto = 'dhcp'

        # TODO Populate DNS information
        #self.dns = self.config.dns

    @property
    def addrs(self):
        ret = dict([(netifaces.address_families[x[0]], x[1])
                    for x in netifaces.ifaddresses(self.name).items()
                    ])
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
    def type(self):
        if self.name.startswith('eth'):
            return 'ethernet'
        elif self.name.startswith('ib'):
            return 'infiniband'
        elif self.name.startswith('lo'):
            return 'local'

    @property
    def netmask(self):
        return str(ipcalc.Network('1.1.1.1/%s' % self.cidr).netmask())

    ## TODO This should probably be a global Config() entry instead of hard-coded crap or being per-interface
    #gateway = models.IPAddressField()
    @property
    def gateway(self):
        return '10.16.38.254'

    ## TODO This should probably be a global Config() entry instead of hard-coded crap or being per-interface
    #dns = JSONField()
    @property
    def dns(self):
        return {'nameservers': ['8.8.8.8', '8.8.4.4'],
                'search': ['solarsan.local'], }

    #def get_absolute_url(self):
    #    return reverse('network-interface-detail', kwargs={'slug': self.name})

    def __unicode__(self):
        if self.ipaddr and self.cidr:
            return '%s (%s/%s)' % (self.name, self.ipaddr, self.cidr)
        else:
            return self.name

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.name)

    @classmethod
    def list(cls):
        ret = {}
        for x in netifaces.interfaces():
            try:
                ret[x] = NetworkInterface(x)
            except:
                pass
        #return dict([(x, lambda NetworkInterface(x) except: None) for x in netifaces.interfaces()])
        return ret
