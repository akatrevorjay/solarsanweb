#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
execfile(os.path.join(os.path.dirname(__file__), 'solarsanweb', 'paths.py'))

#from django.conf import settings
#if settings.DEBUG:
#    try:
#        from dbgp.client import brkOnExcept
#        brkOnExcept(host='localhost', port=9000)
#    except:
#        pass

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
