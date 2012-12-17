from __future__ import with_statement
from django.conf import settings
import sys
import os
import time
from datetime import datetime, timedelta
#import re
import sh
import re
import logging
import configshell

from solarsan.utils import LoggedException, FormattedException
from solarsan.pretty import pp

from . import models, tasks


class Cluster(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Cluster, self).__init__('cluster', parent)
        Neighbors(self)
        Peers(self)


class Neighbors(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Neighbors, self).__init__('neighbors', parent)

        for node in models.Node.objects.all():
            Neighbor(self, node)


class Neighbor(configshell.node.ConfigNode):
    def __init__(self, parent, node):
        self.node = node
        super(Neighbor, self).__init__(node.hostname, parent)


class Peers(configshell.node.ConfigNode):
    def __init__(self, parent):
        super(Peers, self).__init__('peers', parent)

        for peer in models.Peer.objects.all():
            Peer(self, peer)


class Peer(configshell.node.ConfigNode):
    def __init__(self, parent, peer):
        self.peer = peer
        self.node = node = peer.node
        super(Peer, self).__init__(node.hostname, parent)
