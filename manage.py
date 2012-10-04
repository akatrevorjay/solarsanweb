#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
execfile(os.path.join(os.path.dirname(__file__), 'solarsanweb', 'paths.py'))

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
