from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import time

import cluster.service


class Command(BaseCommand):
    help = 'Run SolarSan Cluster ZMQ'
    #args = 'primary'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        cluster.service.main()
