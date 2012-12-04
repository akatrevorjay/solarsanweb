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


class ClusterNode(m.Document):
    meta = {'collection': 'cluster_nodes'}
    hostname = m.StringField(required=True, unique=True)
    # TODO Make this an embedded document
    last_seen = m.DateTimeField()
    first_seen = m.DateTimeField()
    interfaces = m.DictField()
