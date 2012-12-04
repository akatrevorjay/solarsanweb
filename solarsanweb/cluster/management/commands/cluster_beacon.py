from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import time

from beacon import Beacon


class Command(BaseCommand):
    help = 'Run SolarSan Cluster Beacon'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        logging.info("Starting Cluster Beacon..")
        b = Beacon(settings.SOLARSAN_CLUSTER['port'], settings.SOLARSAN_CLUSTER['key'])
        b.daemon = True
        try:
            b.start()
            while True: time.sleep(1000)
        except (KeyboardInterrupt, SystemExit):
            logging.error("Received interrupt, exiting..\n")
