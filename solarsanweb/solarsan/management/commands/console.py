from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
#import os
#import re
import logging
import sh

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

        print 'Pool Health:'
        for pool in Pool.objects.all():
            try:
                alloc = pool.properties['alloc']
                size = pool.properties['size']
                capacity = pool.properties['capacity']
                health = pool.properties['health']
                print '%18s: %14s %20s' % (pool.name,
                                            '%s/%s' % (alloc, size),
                                            health)
            except:
                logging.error("Pool %s is not available", pool)
                print '%18s: %14s %20s' % (pool.name,
                                            '',
                                            'MISSING')

        print ''
        print 'Services:'
        for line in sh.grep(sh.initctl('list'), 'solarsan'):
            line = line.rstrip("\n")
            #name, status, process_text, pid = line.split()
            name, status = line.split(None, 1)
            try:
                status, process_info = status.split(None, 1)
                status = status.rstrip(',')
            except:
                process_info = ''
            name = name.replace('solarsan-', '', 1)
            #line = line.split(None, 2)
            #line[0] = line[0].replace('solarsan-', '', 1)
            #if len(line) == 2:
            #    line[2] = line[1]
            #    line[1] = ''
            print '%18s: %14s %20s' % (name, status, process_info)

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
