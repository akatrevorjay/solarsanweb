#!/usr/bin/env python
import os, sys

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

