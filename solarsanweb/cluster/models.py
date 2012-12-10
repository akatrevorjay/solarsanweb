#from solarsan.models import EnabledModelManager
#from jsonfield import JSONField
from django.db import models
from django.utils import timezone
#from django.core.urlresolvers import reverse
from datetime import datetime, timedelta
import logging

import mongoengine as m


"""
Cluster
"""


class Node(m.Document):
    hostname = m.StringField(required=True, unique=True)
    # TODO Make this an embedded document
    last_seen = m.DateTimeField()
    first_seen = m.DateTimeField()
    interfaces = m.DictField()

    created = m.DateTimeField()
    modified = m.DateTimeField()


class Peer(m.Document):
    node = m.ReferenceField(Node, dbref=False)

    #last_heartbeat_received = m.DateTimeField()
    #last_heartbeat_sent = m.DateTimeField()
    last_heartbeat_at = m.DateTimeField()

    def ping(self):
        pass

    def heartbeat(self):
        pass
