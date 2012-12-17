from __future__ import with_statement
from django.conf import settings
import sys
import os
import time
from datetime import datetime, timedelta
#import re
import sh
import logging
import configshell

from solarsan.utils import LoggedException, FormattedException
from pprint import pprint, pformat

from . import models
from . import tasks

from solarsan.pretty import pp


class Nic(configshell.node.ConfigNode):
    def __init__(self, parent, name, nic):
        self.obj = nic
        super(Nic, self).__init__(name, parent)

    def summary(self):
        try:
            ipv4_addrs = [v['addr'] for v in self.obj.addrs.get('AF_INET')]
            return (', '.join(ipv4_addrs), bool(ipv4_addrs))
        except:
            return ('None', False)

    def ui_command_addrs(self):
        pp(self.obj.addrs)


class Network(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Network, self).__init__('network', parent)

        for name, nic in models.Nic.list().items():
            Nic(self, name, nic)


class System(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(System, self).__init__('system', parent)

    # TODO Attribute or parameter
    def ui_command_hostname(self, hostname=None):
        if not hostname:
            def hostname(*args):
                for line in sh.hostname(*args, _iter=True):
                    return line.rstrip("\n")

            ret = {'hostname': hostname(),
                   'fqdn': hostname('-f'),
                   }
            pp(ret)
        else:
            print "TODO"


class Configure(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Configure, self).__init__('configure', parent)

        Network(self)
        System(self)
