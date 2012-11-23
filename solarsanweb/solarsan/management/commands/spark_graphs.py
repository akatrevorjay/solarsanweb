from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
#import os
#import re

from storage.models import Pool
from spark import spark_string

from pypercube import time_utils
from datetime import timedelta, datetime
from django.utils import timezone


class Command(BaseCommand):
    help = 'Display simple sparkline graphs'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        #stop = time_utils.now()
        #start = time_utils.yesterday(stop)
        #stop = datetime.now()
        #stop = datetime.now() - timedelta(seconds=30)
        stop = datetime.now()
        #start = stop - timedelta(days=60)
        #step = time_utils.STEP_1_DAY
        start = stop - timedelta(hours=1)
        step = time_utils.STEP_1_MIN


        def print_stats(stats):
            for stat in stats:
                stat_name = stat['key']

                if stat_name == 'free':
                    continue

                stat_values = stat['values']
                stat_values.reverse()
                #print '- %s: %s' % (stat_name, stat_values)

                values = [v[1] for v in stat_values[:35]]
                values.reverse()
                #print '- %s:' % stat_name
                print '%18s: %s' % (stat_name, spark_string(values))

        for pool in Pool.objects.all():
        #for pool in [Pool.objects.get(name='sanweb')]:
            print ''
            print '[pool: %s]' % pool.name
            for stats_func in [pool.analytics.iops,
                               pool.analytics.bandwidth,
                               pool.analytics.usage]:
                print_stats(stats_func(start=start,
                                       step=step,
                                       ))

