#
# Basic setup
#

# Paths
import os
from solarsanweb.paths import PROJECT_NAME, TOP_DIR, PROJECT_DIR, DATA_DIR

# Get default settings programattically so we can add to them instead of
# blindly replacing them.
from django.conf import global_settings as gs

#
# Get server name
#

import socket
SERVER_NAME = socket.gethostname()

#
# Get server OS
#

SERVER_OS = os.uname()[0]

SERVER_IS_LINUX = SERVER_OS == 'Linux'
SERVER_IS_KFREEBSD = SERVER_OS == 'GNU/kFreeBSD'

#
# Project Common
#

DEBUG = TEMPLATE_DEBUG = True

ADMINS = (('LocSol', 'crap@localhost'), )
MANAGERS = ADMINS

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jk$cr7u4$8@oj&u+n8&h*h_*g3j8@e3i&pm5k!@h77a8@#j@na'

#
# Databases
#

DATABASES = {
    # TODO If MongoDB is the method moving forward, then this may want to be
    # changed to sqlite for non-compat apps, then use a DatabaseRouter to
    # selectively route queries to the proper db.
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_NAME,                   # Or path to database file if using sqlite3.
        'USER': 'root',                         # Not used with sqlite3.
        'PASSWORD': 'locsol',                   # Not used with sqlite3.
        'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
    },
}

#
# MongoDB (MongoEngine)
#

SERVER_ID = SERVER_NAME

MONGODB_DATABASES = {
    'default': {
        'name': "%s_%s" % (PROJECT_NAME, SERVER_ID),
    },
    'syslog': {
        'name': "syslog",
    },
}

#DJANGO_MONGOENGINE_OVERRIDE_ADMIN = True

import mongoengine


def _register_mongo_databases():
    for k, v in MONGODB_DATABASES.items():
        v = v.copy()
        name = v.pop('name', k)
        mongoengine.register_connection(k, name, **v)
_register_mongo_databases()


# DB Router
#DATABASE_ROUTERS = ['solarsan.routers.MongoDBRouter', ]

# Auth
AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
) + gs.AUTHENTICATION_BACKENDS

# Session Engine
# django.contrib.sessions.backends.cache
# django.contrib.sessions.backends.cached_db
# django_mongoengine.django.sessions
SESSION_ENGINE = 'mongoengine.django.sessions'

#
# Sessions
#

SESSION_COOKIE_NAME = PROJECT_NAME + '_sess'

#
# Django Common
#

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(TOP_DIR, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(TOP_DIR, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# To enable the CachedStaticFilesStorage you have to make sure the following requirements are met:
# . the STATICFILES_STORAGE setting is set to 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'
# . the DEBUG setting is set to False
# . you use the staticfiles static template tag to refer to your static files in your templates
# . you've collected all your static files by using the collectstatic management command
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(TOP_DIR, PROJECT_NAME, "static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = gs.TEMPLATE_CONTEXT_PROCESSORS + (
    "django.contrib.messages.context_processors.messages",  # Is this default or not?
    'django.core.context_processors.request',               # Puts 'request' in context, also required by waffle
    'solarsanweb.storage.context_processors.storage_objects',  # Cause we need em, always.
    'solarsanweb.solarsan.context_processors.site_styles',   # CSS and JS includes
    'solarsanweb.analytics.context_processors.cube',         # Cube url and such
    #'solarsanweb.solarsan.context_processors.raven_dsn',    # Adds raven_dsn for raven-js
    'solarsanweb.solarsan.context_processors.login_form',    # Includes login_form context
)

# Root URL routes
ROOT_URLCONF = '%s.urls' % PROJECT_NAME

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '%s.wsgi.application' % PROJECT_NAME

#
# Apps/Includes/Meh
#

INSTALLED_APPS = (
    #'bootstrap',
    #'coffin',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Uncomment the next lines to enable the admin:
    #'django_mongoengine.auth',
    #'django_mongoengine.admin.sites',
    #'django_mongoengine.admin',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',

    # Third party libs
    'djcelery',
    'djcelery.transport',
    'django_extensions',
    'south',
    #'djsupervisor',

    #'devserver',

    #'sentry',
    #'raven.contrib.django',
    'breadcrumbs',
    'jsonify',
    #'django_logtail',

    #'bootstrap_toolkit',
    'crispy_forms',

    #'jstemplate',

    'rest_framework',
    'rest_framework.authtoken',

    #'tastypie',
    #'tastypie_mongoengine',
    #'backbone_tastypie',

    # For future use
    #'django_utils',                     # this is django-utils2 in PyPi
    #'django_assets',
    #'kitsune',
    #'waffle',
    #'uwsgi_admin',
    #'sitetree',
)

#
# Project Apps
#

PROJECT_APPS = (
    'solarsan',
    'status',
    'configure',
    'cluster',
    'logs',
    'storage',
    'analytics',
    'zfs',
    #'formtest',
)

#PROJECT_APPS = tuple(map(lambda x: 'solarsanweb.'+x, PROJECT_APPS))
INSTALLED_APPS += PROJECT_APPS

#
# Middleware
#

MIDDLEWARE_CLASSES = (
    #'waffle.middleware.WaffleMiddleware',                       # waffle
) + gs.MIDDLEWARE_CLASSES + (
    'breadcrumbs.middleware.BreadcrumbsMiddleware',             # Breadcrumbs
    'django.middleware.http.ConditionalGetMiddleware',          # Allows Vary, Last-Modified-Since, etc
    #'solarsan.middleware.RequireLoginMiddleware',               # Require login across whole site, broken
    #'django.middleware.gzip.GZipMiddleware',                    # Compress output
)

"""
#
# django-logtail
#

# Logs to tail
LOGTAIL_FILES = {
    #'syslog': '/var/log/syslog',
    'solarvisor': DATA_DIR + '/log/supervisord.log',
}
"""

#
# django-ztask
#

#INSTALLED_APPS += ('django_ztask', )
#ZTASKD_URL = 'tcp://127.0.0.1:5555'
#ZTASKD_ALWAYS_EAGER = False
#ZTASKD_DISABLED = False
#ZTASKD_RETRY_COUNT = 5
#ZTASKD_RETRY_AFTER = 5
#ZTASKD_ON_LOAD = ()

#
# django-crispy-forms
#

CRISPY_FAIL_SILENTLY = not DEBUG

##
## 3rd party addins and such
##

#
# Cube
#

CUBE_HOST = 'localhost'
CUBE_COLLECTOR_URL = 'udp://%s:1180' % CUBE_HOST

"""
#
# django-pdb
#

if DEBUG:
    INSTALLED_APPS += ('django_pdb', )
    MIDDLEWARE_CLASSES += ('django_pdb.middleware.PdbMiddleware', )
"""

"""
#
# django-ipython-notebook
#

if DEBUG:
    INSTALLED_APPS += ('django_ipython_notebook', )
"""

#
# Smuggler
#   DB fixture manager
#

#if DEBUG:
#    INSTALLED_APPS += ('smuggler', )

#
# devserver
#

if DEBUG:
    INSTALLED_APPS += ('devserver', )
    MIDDLEWARE_CLASSES += ('devserver.middleware.DevServerMiddleware', )
    DEVSERVER_MODULES = (
        'devserver.modules.sql.SQLRealTimeModule',
        'devserver.modules.sql.SQLSummaryModule',
        'devserver.modules.profile.ProfileSummaryModule',

        # Modules not enabled by default
        'devserver.modules.ajax.AjaxDumpModule',
        #'devserver.modules.profile.MemoryUseModule',
        'devserver.modules.cache.CacheSummaryModule',
        'devserver.modules.profile.LineProfilerModule',
    )
    #DEVSERVER_ARGS = ['--werkzeug', ]
    #DEVSERVER_AUTO_PROFILE = True

#
# SpeedTracer
#

#if DEBUG:
#    INSTALLED_APPS += ('speedtracer', )
#    MIDDLEWARE_CLASSES += ('speedtracer.middleware.SpeedTracerMiddleware', )

#
# django-debug-toolbar
#

if DEBUG:
    INSTALLED_APPS += (
        'debug_toolbar',
        'debug_toolbar_mongo',
        #'django_mongoengine.debug_toolbar',  # Has some major speed problems, but is better at what it does.
    )
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',          # Enable django-debug-toolbar
    )

    #DEBUG_TOOLBAR_MONGO_STACKTRACES = False

    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
        'debug_toolbar.panels.cache.CacheDebugPanel',
        'debug_toolbar_mongo.panel.MongoDebugPanel',
        #'django_mongoengine.debug_toolbar.panel.MongoDebugPanel',
    )

    def custom_show_toolbar(request):
        return True  # HACK
        try:
            if request.is_ajax():
                return False
            #if DEBUG: return True              # Show if DEBUG; default == DEBUG and if source ip in INTERNAL_IPS
            return request.user.is_superuser    # Show if logged in as a superuser
        except:
            return False

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
        'HIDE_DJANGO_SQL': False,
        #'TAG': 'div',
        'ENABLE_STACKTRACES': True,
        'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    }

    INTERNAL_IPS = ['127.0.0.1']

#
# django-supervisor
#

#SUPERVISOR_CONFIG_FILE = os.path.join(TOP_DIR, 'conf', 'supervisord.conf')

#
# jstemplate
#

#JSTEMPLATE_DIRS = (
#    os.path.join(PROJECT_DIR, "templates", "jstemplates"),
#)

#for x in PROJECT_APPS:
#    JSTEMPLATE_DIRS += (os.path.join(PROJECT_DIR, x, "templates", "jstemplates"), )

#
# Auth
#

#AUTHENTICATION_BACKENDS += (
#    # Needed to login by username in Django admin, regardless of `allauth`
#    #"django.contrib.auth.backends.ModelBackend",
#    # `allauth` specific authentication methods, such as login by e-mail
#    #"allauth.account.auth_backends.AuthenticationBackend",
#)

# Password hash priority (and what's allowed)
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

# User pofile class replacement
#AUTH_PROFILE_MODULE = 'solarsan.models.UserProfile'

#
# Cache backend
#

CACHES = {
    #'default_mem': {
    #    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    #    'LOCATION': PROJECT_NAME,
    #},
    #'default_db': {
    #    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    #    'LOCATION': PROJECT_NAME+'_django_db_cache',
    #},
    'default_file': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(DATA_DIR, 'cache'),
    },
    #'default_mongodb': {
    #    'BACKEND': 'solarsan.cache.EasyGoingMongoDBCache',
    #    'database': PROJECT_NAME,
    #    #'LOCATION': '%s_django_db_cache__%s' % (PROJECT_NAME, SERVER_NAME),
    #    'LOCATION': 'localhost',
    #},
}

CACHES['default'] = CACHES.pop('default_file')
#CACHES['default'] = CACHES.pop('default_mongodb')
#CACHES['default'] = CACHES.pop('default_db')

#
# Template related
#

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

#
# Celery (async tasks)
#

from kombu import Exchange, Queue
from kombu.common import Broadcast
import djcelery
djcelery.setup_loader()

#CELERYBEAT_SCHEDULER = "solarsanweb.solarsan.utils.CeleryBeatScheduler"
CELERY_TIMEZONE = TIME_ZONE
#CELERYD_CONCURRENCY = 25

# Celery broker
#BROKER_URL = "amqp://solarsan:Thahnaifee1ichiu8hohv5boosaengai@localhost:5672/solarsan"
#BROKER_URL = "pyamqp://solarsan:Thahnaifee1ichiu8hohv5boosaengai@localhost:5672/solarsan"
BROKER_URL = "librabbitmq://solarsan:Thahnaifee1ichiu8hohv5boosaengai@localhost:5672/solarsan"
#BROKER_USE_SSL = True
#CELERY_DEFAULT_RATE_LIMIT = "50/s"  # 100/s
CELERY_DISABLE_RATE_LIMIT = True
BROKER_CONNECTION_MAX_RETRIES = "50"  # 100
CELERYD_MAX_TASKS_PER_CHILD = "100"

# Celery results
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hrs
#CELERY_RESULT_BACKEND = "amqp"
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "database": MONGODB_DATABASES['default']['name'],
    "host": MONGODB_DATABASES['default'].get('host', None),
}

#default_exchange = Exchange('default', type='direct')
#media_exchange = Exchange('media', type='direct')

# Celery extra opts
CELERY_QUEUES = (
    #Queue('default', Exchange('default'), routing_key='default'),
    Queue('box_%s' % SERVER_NAME, Exchange('tasks'), durable=True, routing_key='box_%s' % SERVER_NAME, queue_arguments={'x-ha-policy': 'all'}),
    Queue('shared', Exchange('shared'), durable=True, routing_key='shared', queue_arguments={'x-ha-policy': 'all'}),
    #Broadcast('shared_broadcast', Exchange('shared_broadcast'), routing_key='shared_broadcast', queue_arguments={'x-ha-policy': 'all'}),
    Broadcast('shared_broadcast'),
)

#CELERY_DEFAULT_EXCHANGE = "celery"
CELERY_DEFAULT_EXCHANGE = "tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_QUEUE = "box_%s" % SERVER_NAME
CELERY_DEFAULT_ROUTING_KEY = 'box_%s' % SERVER_NAME

#CELERY_ROUTES = ({"myapp.tasks.compress_video": {
#                        "queue": "video",
#                        "routing_key": "video.compress"
#                 }}, )
#CELERY_CREATE_MISSING_QUEUES

# Send events when debugging
if DEBUG:
    CELERY_SEND_EVENTS = True
    CELERY_SEND_TASK_SENT_EVENT = True
    CELERY_TRACK_STARTED = True

# Extra task modules (def = [INSTALLED_APPS].tasks)
CELERY_IMPORTS = (
    'celery.task.http',  # Enable HTTP dispatch task (http://celery.github.com/celery/userguide/remote-tasks.html)
)

#
# Logging
#

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    #'disable_existing_loggers': True,
    #'disable_existing_loggers': False,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'syslog'],
        #'level': 'WARNING',
        #'handlers': ['console', 'sentry'],
    },

    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s.%(module)s@%(funcName)s:%(lineno)d %(message)s',
            #'datefmt': '%d/%b/%Y %H:%M:%S',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'syslog': {
            #'format': '<22>%(asctime)s ' + SERVER_NAME + ' %(name)s[%(process)d]: %(message)s',
            #'format': 'solarsan.%(name)s[%(process)d]: %(levelname)s %(message)s',
            #'format': 'solarsan/%(name)s.%(module)s/%(processName)s[%(process)d]: %(levelname)s %(message)s @%(funcName)s:%(lineno)d',
            'format': 'solarsan/%(name)s.%(module)s/%(processName)s[%(process)d]: %(message)s @%(funcName)s:%(lineno)d',
            #'celery_format': 'solarsan/%(name)s[%(process)d]: %(levelname)s %(message)s @%(funcName)s:%(lineno)d',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        #'sentry': {
        #    'level': 'DEBUG',
        #    'class': 'raven.contrib.django.handlers.SentryHandler',
        #},
        #'mail_admins': {
        #    'level': 'ERROR',
        #    'class': 'django.utils.log.AdminEmailHandler',
        #},
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            #'class': 'logging.StreamHandler',
            'class': 'ConsoleHandler.ConsoleHandler',
            'formatter': 'standard',
        },
        'syslog': {
            'level': 'DEBUG',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslog',
            'address': '/dev/log',
        },
    },
    'loggers': {
        'django.db': {
            'propagate': True,
            #'level': 'DEBUG',
            'level': 'INFO',
        },
    }
}

#
# Celery mongo logging
#

CELERYD_LOG_COLOR = False
#CELERYD_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
#CELERYD_LOG_FORMAT = 'solarsan/%(name)s[%(process)d]: %(levelname)s %(message)s @%(funcName)s:%(lineno)d'
CELERYD_LOG_FORMAT = 'solarsan/%(name)s[%(process)d]: %(message)s @%(funcName)s:%(lineno)d'
#CELERYD_TASK_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"
#CELERYD_TASK_LOG_FORMAT = 'solarsan/%(task_name)s[%(task_id)s]: %(levelname)s %(message)s @%(funcName)s:%(lineno)d'
CELERYD_TASK_LOG_FORMAT = 'solarsan/%(task_name)s[%(task_id)s]: %(message)s @%(funcName)s:%(lineno)d'
#CELERYD_LOG_LEVEL = 'INFO'

import logging
from celery.signals import after_setup_logger, after_setup_task_logger


def after_setup_logger_handler(sender=None, logger=None, loglevel=None,
                               logfile=None, format=None,
                               colorize=None, **kwds):
    syslog_hand = LOGGING['handlers']['syslog']
    #syslog_fmt = LOGGING['formatters']['syslog']['celery_format']

    handler = logging.handlers.SysLogHandler(address=syslog_hand['address'])
    #handler.setFormatter(logging.Formatter(syslog_fmt))
    handler.setFormatter(logging.Formatter(format))
    #handler.setLevel(getattr(logging, syslog_hand['level'], logging.INFO))
    handler.setLevel(loglevel)
    logger.addHandler(handler)

after_setup_logger.connect(after_setup_logger_handler)
after_setup_task_logger.connect(after_setup_logger_handler)

"""
#
# allauth / social auth
#

INSTALLED_APPS += (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.linkedin',
    'allauth.socialaccount.providers.openid',
    'allauth.socialaccount.providers.persona',
    'allauth.socialaccount.providers.soundcloud',
    'allauth.socialaccount.providers.twitter',
)

SOCIALACCOUNT_PROVIDERS = {
    #'google':
    #    { 'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile'] },
    #'openid':
    #    { 'SERVERS':
    #        [dict(id='yahoo',
    #              name='Yahoo',
    #              openid_url='http://me.yahoo.com'),
    #         dict(id='hyves',
    #              name='Hyves',
    #              openid_url='http://hyves.nl'),
    #         dict(id='google',
    #              name='Google',
    #              openid_url='https://www.google.com/accounts/o8/id')]},
    'persona': {
        'REQUEST_PARAMETERS': {'siteName': 'SolarSan Console'},
    },
}

TEMPLATE_CONTEXT_PROCESSORS += (
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
)
"""

"""
#
# django-compressor
#

INSTALLED_APPS += ('compressor', )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'compressor.finders.CompressorFinder',
) + STATICFILES_FINDERS

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    #('text/less', 'lessc {infile} {outfile}'),
    ('text/less', 'recess --compile {infile}'),
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass --scss {infile} {outfile}'),
)

COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
    #'compressor.filters.jsmin.SlimItFilter',
    #'compressor.filters.closure.ClosureCompilerFilter',
    #'compressor.filters.yui.YUIJSFilter',
    #'compressor.filters.template.TemplateFilter',
]

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    #'compressor.filters.csstidy.CSSTidyFilter',
    #'compressor.filters.datauri.CssDataUriFilter',
    #'compressor.filters.yui.YUICSSFilter',
    'compressor.filters.cssmin.CSSMinFilter',
    #'compressor.filters.template.TemplateFilter',
]

if DEBUG:
    COMPRESS_DEBUG_TOGGLE = 'nocompress'
#COMPRESS_OFFLINE = True
#COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'
COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
#COMPRESS_CACHE_BACKEND = 'default'
COMPRESS_ENABLED = True
"""

"""
#
# django-bootstrap-toolkit
#

BOOTSTRAP_BASE_URL = '/static/bootstrap/'
BOOTSTRAP_CSS_BASE_URL = BOOTSTRAP_BASE_URL + 'css/'
BOOTSTRAP_CSS_URL = BOOTSTRAP_CSS_BASE_URL + 'bootstrap.css'
BOOTSTRAP_JS_BASE_URL = BOOTSTRAP_BASE_URL + 'js/'
# Enable for single bootstrap.js file
BOOTSTRAP_JS_URL = BOOTSTRAP_JS_BASE_URL + 'bootstrap.js'
"""

#
# djangorestframework
#

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
        #'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.JSONPRenderer',
        'rest_framework.renderers.YAMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.XMLRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer',
    ),
    #'DEFAULT_PARSER_CLASSES': (
    #    'rest_framework.parsers.JSONParser',
    #    'rest_framework.parsers.FormParser'
    #),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        #'rest_framework.authentication.UserBasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'PAGINATE_BY': 10,
}
