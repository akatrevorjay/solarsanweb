#!/usr/bin/env python
import os, sys

#sys.path.insert(0, '/home/trevorj/.eclipse/Aptana_Studio_3_Setup_Linux_x86_64_3.1.3/plugins/org.python.pydev_2.6.0.2012052102/pysrc')
#
# PyDev Run Autoreload
#TODO Check for new env var set in Eclipse or check if pydevd exists first
#import pydevd
#pydevd.patch_django_autoreload(
#    #patch_remote_debugger=False, #Note that the remote debugger patch setting should be False on a regular run
#    #patch_show_console=True
#    patch_remote_debugger=True, #Connect to the remote debugger.
#    patch_show_console=True
#)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solarsanweb.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

