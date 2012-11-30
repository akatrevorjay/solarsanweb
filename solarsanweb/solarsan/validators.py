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
Validators
"""
# TODO Move this elsewhere


class MinLengthValidator(object):
    def __init__(self, min_length):
        self.min_length = min_length
    def __call__(self, value):
        if not len(value) >= self.min_length:
            raise Exception('%s must be at least ' + str(self.min_length) + ' characters long.')


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


    validators = {
        #'hostname': RegexValidator(r'^[a-z0-9]+$', re.IGNORECASE),
    }

    def validate(self, *args, **kwargs):
        v_iface_name = re.compile(r'^((eth|ib)\d{1,2}|lo)$', re.IGNORECASE)
        v_afs = netifaces.address_families.values()
        for iface_name,iface in self['interfaces'].iteritems():
            assert bool(v_iface_name.match(iface_name))
            #if not bool(v_iface_name.match(iface_name)):
            #    continue
            for af, addrs in iface.iteritems():
                assert af in v_afs
                for ip,mask in addrs:
                    #try:
                    ip = ipcalc.Network( "%s/%s" % (ip, mask) )
                    #except:
                    #    addrs.remove([ip,mask])
                    #    #assert False
        super(ClusterNode, self).validate(*args, **kwargs)


