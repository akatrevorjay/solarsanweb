from django.db import models
from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import zfs

from django_mongokit import connection
from django_mongokit.document import DjangoDocument
import datetime
from django.utils import timezone

from storage.models import zPool, zDataset

class ReplicationJob(DjangoDocument):
    use_autorefs = True
    collection_name = 'replication_job'
    structure = {
            'dataset': zDataset,
            'snap_from': zDataset,
            'snap_to': zDataset,
            'active': bool,
            'status': dict,

            'started': datetime.datetime,
            'last_updated': datetime.datetime,
    }
    default_values = {
            'last_updated': timezone.now(),
            'started': timezone.now(),
    }


