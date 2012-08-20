from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
#import os
#import re

class Command(BaseCommand):
    help = 'Run SolarSan Console Monitor'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        # don't add django internal code
        print "yupyup"


from spark import spark_string



logo = ('                                                        '
        '               ""#                                      '
        '  mmm    mmm     #     mmm    m mm   mmm    mmm   m mm  '
        ' #   "  #" "#    #    "   #   #"  " #   "  "   #  #"  # '
        '  """m  #   #    #    m"""#   #      """m  m"""#  #   # '
        ' "mmm"  "#m#"    "mm  "mm"#   #     "mmm"  "mm"#  #   # '
        '                                                        ')
sep =  ('::::::::::::::::::::::::::::::::::::::::::::::  F L U X ')
crap = (''
        ' Pool Health:                                    [  Y  ] '
        ' - dpool (59.7G/11.7T)                           [  Y  ] '
        ' Filesystem Health:                              [  Y  ] '
        ' - dpool/* (59.7G/11.7T)                         [  Y  ] '
        ''
        ' Scheduler:                                      [  Y  ] '
        ' Web Interface:                                  [  Y  ] '
        ' Logging API:                                    [  Y  ] '
        ' Message Queue:                                  [  Y  ] '
        ''
        ' Cluster:                                        [  Y  ] '
        ' - Replication: (1 x 2 = 2)                      [  Y  ] '
        ' - Volume Health:                                [  Y  ] '
        ' - Raging Data Eater:                            [  N  ] '
        ''
        ' ------------------------------------------------------- '
        ' >> getty -> \n -> \l')



