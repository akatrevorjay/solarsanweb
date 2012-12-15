#from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
#from django.conf import settings
#import sys
#import os
#import time
#from datetime import datetime, timedelta
##import re
#import sh
#import logging
#import configshell
#from solarsan.utils import LoggedException, FormattedException

from solarsan.cli import *


class Command(BaseCommand):
    help = 'Run SolarSan Cli'
    #args = 'tag'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        main()
