#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

PROJECT_NAME = 'solarsanweb'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings' % PROJECT_NAME)

def _find_project(try_dir=None, max_depth=5):
    if not try_dir:
        #try_dir = os.path.relpath(os.path.dirname(os.path.realpath(__file__)))
        try_dir = os.path.dirname(os.path.realpath(__file__))
    if os.path.isfile(os.path.join(try_dir, '.%s.top' % PROJECT_NAME)):
        #return os.path.realpath(try_dir)
        return os.path.relpath(try_dir)
        #return try_dir
    elif max_depth == 0:
        raise Exception('Could not find project top directory')
    else:
        max_depth -= 1
        return _find_project(os.path.join(try_dir, os.path.pardir), max_depth=max_depth)

TOP_DIR = _find_project()
PROJECT_DIR = os.path.join(TOP_DIR, PROJECT_NAME)
DATA_DIR = os.path.join(TOP_DIR, 'data')

sys.path.insert(0, os.path.join(TOP_DIR, 'vendor-local'))
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, TOP_DIR)
