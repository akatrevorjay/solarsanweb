from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import time

import cluster.discovery


class Command(BaseCommand):
    help = 'Run SolarSan Cluster Discovery'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        cluster.discovery.main()
