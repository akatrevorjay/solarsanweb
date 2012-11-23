from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
#import os
#import re

from storage.models import Pool


class Command(BaseCommand):
    help = 'Run SolarSan Console Monitor'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        # don't add django internal code
        logo = ('                                                        ',
                '               ""#                                      ',
                '  mmm    mmm     #     mmm    m mm   mmm    mmm   m mm  ',
                ' #   "  #" "#    #    "   #   #"  " #   "  "   #  #"  # ',
                '  """m  #   #    #    m"""#   #      """m  m"""#  #   # ',
                ' "mmm"  "#m#"    "mm  "mm"#   #     "mmm"  "mm"#  #   # ',
                '                                                        ')
        sep =  ('::::::::::::::::::::::::::::::::::::::::::::::  F L U X ',
                )

        for i in logo + sep:
            print i

        print ''

        print ' Pool Health:'
        for pool in Pool.objects.all():
            alloc = pool.properties['alloc']
            size = pool.properties['size']
            capacity = pool.properties['capacity']
            health = pool.properties['health']
            print '%16s: %14s %22s' % (pool.name,
                                         '%s/%s' % (alloc, size),
                                         health)

        crap = (
                '',
                ' Scheduler:                                     [  Y  ] ',
                ' Web Interface:                                 [  Y  ] ',
                ' Logging API:                                   [  Y  ] ',
                ' Message Queue:                                 [  Y  ] ',
                '',
                ' Cluster:                                       [  Y  ] ',
                ' - Replication: (1 x 2 = 2)                     [  Y  ] ',
                ' - Volume Health:                               [  Y  ] ',
                ' - Raging Data Eater:                           [  N  ] ',
                '',
                ' ------------------------------------------------------ ',
                ' >> getty -> \n -> \l')

        #for i in crap:
        #    print i

        print ''
