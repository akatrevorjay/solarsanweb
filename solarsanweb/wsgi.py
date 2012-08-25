#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI config for solarsanweb project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""

import os
execfile(os.path.join(os.path.dirname(__file__), os.path.pardir, 'paths.py'))

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

## Apparently this is needed here?
## http://celery.github.com/celery/django/first-steps-with-django.html#configuring-your-django-project-to-use-celery
import djcelery
djcelery.setup_loader()

##
## Allow autoreload to work properly with uwsgi
##

try:
    import uwsgi
    from uwsgidecorators import timer
    # from uwsgidecorators import *
    # @timer(30, target='spooler')
    # def hello_world(signum):
    #        print("30 seconds elapsed")

    from django.utils import autoreload
    from django.conf import settings

    if settings.DEBUG:
        @timer(3)
        def change_code_gracefull_reload(sig):
            if autoreload.code_changed():
                uwsgi.reload()
except:
    pass
