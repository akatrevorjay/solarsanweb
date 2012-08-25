#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

if __name__ == '__main__':
    execfile(os.path.join(os.path.dirname(__file__), 'conf', 'project_exec.py'))
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
