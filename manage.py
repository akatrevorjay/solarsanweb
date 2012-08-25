#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

execfile(os.path.join(os.path.dirname(__file__), 'conf', 'project_exec.py'))

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarsanweb.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
