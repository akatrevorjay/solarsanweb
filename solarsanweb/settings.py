# Django settings for solarsanweb project.

PROJECT_NAME = "solarsanweb"

import socket
SERVER_NAME = socket.gethostname()

##
## Paths
##

import os, sys

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PROJECT_DIR = os.path.join(TOP_DIR, PROJECT_NAME)
DATA_DIR = os.path.join(TOP_DIR, "data")

for i in ['vendor', 'vendor-local']:
    sys.path.insert(0, os.path.join(TOP_DIR, i))

sys.path.insert(0, os.path.join(PROJECT_DIR, 'lib'))
sys.path.insert(0, PROJECT_DIR)

##
## Project Common
##

DEBUG = TEMPLATE_DEBUG = True

ADMINS = ( ('LocSol', 'info@localhostsolutions.com'), )
MANAGERS = ADMINS

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jk$cr7u4$8@oj&u+n8&h*h_*g3j8@e3i&pm5k!@h77a8@#j@na'

DATABASES = {
    ## TODO If MongoDB is the method moving forward, then this may want to be changed to sqlite for non-compat apps, then use a DatabaseRouter to selectively
    ##   route queries to the proper db.
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_NAME,                 # Or path to database file if using sqlite3.
        'USER': 'root',                       # Not used with sqlite3.
        'PASSWORD': 'locsol',                 # Not used with sqlite3.
        'HOST': '',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                           # Set to empty string for default. Not used with sqlite3.
    },

    ## MongoDB
    'mongodb': {
        'ENGINE': 'django_mongodb_engine',
        #'ENGINE': 'django_mongokit.mongodb',
        'NAME': PROJECT_NAME,
    },
}

DATABASE_ROUTERS = ['django_mongodb_engine.router.MongoDBRouter',]

##
## MongoDB -- mongoengine
##

## Use MongoDB for Auth
AUTHENTICATION_BACKENDS = ( 'mongoengine.django.auth.MongoEngineBackend', )
#AUTHENTICATION_BACKENDS = ( 'permission_backend_nonrel.backends.NonrelPermissionBackend', )

from mongoengine import connect
connect(PROJECT_NAME)

##
## Django Common
##

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'
USE_TZ = True

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
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Defaults for Django 1.4
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",

    # Not default
    "django.contrib.messages.context_processors.messages",  # Is this default or not?
    'django.core.context_processors.request',               # Puts 'request' in context, also required by waffle
    'solarsanweb.solarsan.context_processors.pools',        # This always puts 'pools' list in context (for top nav)
)

## Root URL routes
ROOT_URLCONF = PROJECT_NAME + '.urls'

## Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = PROJECT_NAME + '.wsgi.application'

##
## Apps/Includes/Meh
##

INSTALLED_APPS = (
    # This has to be first, as I had to comment out it's nasty prepending.
    #'django_mongodb_engine',
    'bootstrap',
    'coffin',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next lines to enable the admin:
    #'mongoadmin',
    #'mongonaut',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',

    # Nonrel related
    'djangotoolbox',
    #'permission_backend_nonrel',

    # Third party libs
    'djcelery',
    #'djkombu.transport',
    #'djcelery.transport',
    'django_extensions',
    'south',

    # For future use
    'djsupervisor',
    'crispy_forms',
    #'django_assets',
    #'kitsune',
    'waffle',

    # Debug toolbar
    'debug_toolbar',
    'debug_toolbar_user_panel',
    'cache_panel',
    'debug_toolbar_mongo',
    'debug_toolbar_htmltidy',
)

PROJECT_APPS = (
    'solarsan',
    'status',
    'configure',
    'storage',
    'analytics',
    #'formtest',
)

#PROJECT_APPS = tuple(map(lambda x: 'solarsanweb.'+x, PROJECT_APPS))
INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS

## Enable some apps when debugging
if DEBUG: INSTALLED_APPS = INSTALLED_APPS + (
        'smuggler',         # DB fixture manager
        #'speedtracer',
    )

## List of apps/models that should use mongo.
MONGODB_MANAGED_APPS = (
    'solarsan',
    'status',
    #'configure',
    #'storage',         # TODO remove requirement on .id in Import_ZFS_Metadata
    'analytics',       # TODO convert data to fixture

    #'debug_toolbar',
    #'debug_toolbar_user_panel',
    #'cache_panel',
    'debug_toolbar_mongo',

    'djangotoolbox',
    #'django_mongodb_engine',
    #'django.contrib.auth',
    #'djcelery',
    #'smuggler',

    'permission_backend_nonrel',
    #'mongonaut',

    #'raven.contrib.django',
)

MONGODB_MANAGED_MODELS = (
)

## Use this if mongoadmin should override django.contrib.admin.site with mongoadmin.site
#MONGOADMIN_OVERRIDE_ADMIN = True

## List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'coffin.template.loaders.Loader',
)

JINJA2_TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)

JINJA2_DISABLED_TEMPLATES = (
    'debug_toolbar', 'debug_toolbar_user_panel', 'cache_panel', 'debug_toolbar_mongo', r'mongo-[^/]+\.html', 'debug_toolbar_htmltidy',
    'admin', 'registration',
    'logs',
    'kitsune',
    'crispy_forms',
    'mongonaut',
    'speedtracer',

    #r'[^/]+\.html',                           # All generic templates
    #r'myapp/(registration|photos|calendar)/', # The three apps in the myapp package
    #r'auth/',                                 # All auth templates
    #r'(cms|menu|admin|admin_doc)/',           # The templates of these 4 apps
)

##
## Middleware
##

MIDDLEWARE_CLASSES = (
    'waffle.middleware.WaffleMiddleware',                       # waffle

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',     # Enable Session support
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.gzip.GZipMiddleware',                    # Compress output
    'django.middleware.http.ConditionalGetMiddleware',          # Allows Vary, Last-Modified-Since, etc
    'debug_toolbar.middleware.DebugToolbarMiddleware',          # Enable django-debug-toolbar

    'solarsan.middleware.RequireLoginMiddleware',               # Require login across whole site
)

if DEBUG: MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
        #'speedtracer.middleware.SpeedTracerMiddleware',             # SpeedTracer
    )

## MongoNaut
#MONGONAUT_JQUERY = "http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"
#MONGONAUT_TWITTER_BOOTSTRAP = "http://twitter.github.com/bootstrap/assets/css/bootstrap.css"
#MONGONAUT_TWITTER_BOOTSTRAP_ALERT = http://twitter.github.com/bootstrap/assets/js/bootstrap-alert.js"

##
## django-debug-toolbar
##

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
    'debug_toolbar_user_panel.panels.UserPanel',
    'cache_panel.CachePanel',
    'debug_toolbar_mongo.panel.MongoDebugPanel',
    'debug_toolbar_htmltidy.panels.HTMLTidyDebugPanel',
)

#DEBUG_TOOLBAR_MONGO_STACKTRACES = False

def custom_show_toolbar(request):
    #if DEBUG: return True              # Show if DEBUG; default == DEBUG and if source ip in INTERNAL_IPS
    return request.user.is_superuser    # Show if logged in as a superuser

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
    'ENABLE_STACKTRACES' : True,
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
}

INTERNAL_IPS=['127.0.0.1']

## Password Hash Priority (and what's allowed)
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

## User Profile Class
#AUTH_PROFILE_MODULE = 'solarsan.models.UserProfile'

##
## Cache backend
##

CACHES = {
    #'default_mem': {
    #    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    #    'LOCATION': PROJECT_NAME,
    #},
    #'default_db': {
    #    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    #    'LOCATION': PROJECT_NAME+'_django_db_cache',
    #},
    #'default_file': {
    #    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    #    'LOCATION': os.path.join(DATA_DIR, 'cache'),
    #},
    'default_mongodb': {
        'BACKEND': 'django_mongodb_cache.MongoDBCache',
        'LOCATION': '%s_django_db_cache__%s' % (PROJECT_NAME, SERVER_NAME),
    },
}

#if DEBUG:   CACHES['default'] = CACHES['default_mem']
#else:       CACHES['default'] = CACHES['default_db']
#else:       CACHES['default'] = CACHES['default_file']
CACHES['default'] = CACHES['default_mongodb']

## Persistent sessions
#if DEBUG:   SESSION_ENGINE = "django.contrib.sessions.backends.cache"
#else:       SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
#else:       SESSION_ENGINE = 'mongoengine.django.sessions'
#SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_ENGINE = 'mongoengine.django.sessions'

##
## Jinja2/Coffin Templates
##

#JINJA2_FILTERS = (
#    #'path.to.myfilter',
#)

#JINJA2_TESTS = {
#    #'test_name': 'path.to.mytest',
#}

JINJA2_EXTENSIONS = (
    'jinja2.ext.do', 'jinja2.ext.i18n', 'jinja2.ext.with_', 'jinja2.ext.loopcontrols',
    #'compressor.contrib.jinja2ext.CompressorExtension',
)

#from jinja2 import StrictUndefined
#JINJA2_ENVIRONMENT_OPTIONS = {
#    #'autoescape': False,
#    #'undefined': StrictUndefined,
#    #'autoreload': True,                # Is this needed with coffin or just jingo?
#}

# Monkeypatch Django to mimic Jinja2 behaviour (related to autoescaped strings)
from django.utils import safestring
if not hasattr(safestring, '__html__'):
    safestring.SafeString.__html__ = lambda self: str(self)
    safestring.SafeUnicode.__html__ = lambda self: unicode(self)

##
## Celery (async tasks)
##

## django-celery
import djcelery
djcelery.setup_loader()
#CELERYBEAT_SCHEDULER = "solarsanweb.solarsan.utils.CeleryBeatScheduler"

## Celery broker
BROKER_URL = "amqp://solarsan:Thahnaifee1ichiu8hohv5boosaengai@localhost:5672/solarsan"
#BROKER_USE_SSL = True
CELERY_RESULT_BACKEND = "amqp"
#CELERY_DEFAULT_RATE_LIMIT = "100/s"

## Celery extra opts
CELERY_QUEUES = {
    'box_%s' % SERVER_NAME: {'binding_key': 'box_%s' % SERVER_NAME},
    'shared':               {'binding_key': 'shared'},
}

#CELERY_DEFAULT_EXCHANGE = "celery"
CELERY_DEFAULT_EXCHANGE = "tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_QUEUE = "box_" + SERVER_NAME
CELERY_DEFAULT_ROUTING_KEY = 'box_%s' % SERVER_NAME

#CELERY_ROUTES = ({"myapp.tasks.compress_video": {
#                        "queue": "video",
#                        "routing_key": "video.compress"
#                 }}, )
#CELERY_CREATE_MISSING_QUEUES

## Send events when debugging
if DEBUG:
    CELERY_SEND_EVENTS = True
    CELERY_SEND_TASK_SENT_EVENT = True

## Extra task modules (def = [INSTALLED_APPS].tasks)
CELERY_IMPORTS = (
    #"solarsan.tasks.locsol_backup",
    #"solarsan.tasks.cluster",

    ## Enable HTTP dispatch task (http://celery.github.com/celery/userguide/remote-tasks.html)
    'celery.task.http',
)

##
## Logging
##

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    #'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(filename)s@%(funcName)s:%(lineno)d %(message)s',
            #'datefmt': '%d/%b/%Y %H:%M:%S',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'sentry': {
            'level': 'DEBUG',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
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
    },
    'loggers': {
        #'django': {
        #    'handlers':['console'],
        #    'propagate': True,
        #    'level':'INFO',
        #},
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        #'apps': {
        #    'handlers': ['console',],
        #    'level': 'DEBUG',
        #},
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}


##
## Sentry/Raven
##

RAVEN_CONFIG = {
    'dsn': 'http://7774c7fd239647f290af254c36d6153c:796e31c848d74c4b9f9fab04abdf62a5@sentry.solarsan.local/2',
    'register_signals': True,
}

# Add raven to the list of installed apps
INSTALLED_APPS = INSTALLED_APPS + (
    #'raven.contrib.django',
)

from raven.contrib.django.models import client
client.captureException()

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'raven.contrib.django.middleware.Sentry404CatchMiddleware',         # Catch 404s
    'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',  # Catch Errors
)

##
## SolarSan Log UI
##

# Logs to tail
LOGTAIL_FILES = {
    'syslog': '/var/log/syslog',
    'solarvisor': '/opt/solarsanweb/data/log/supervisord.log',
    # gluster
}


##
## SolarSan Cluster
##
## TODO Make key configurable, put it in the DB and in the UI.
SOLARSAN_CLUSTER = {
    'port':         1787,               # Port = 1337 * 1.337
    'key':          'solarsan-key0',    # Key
    'discovery':    25,                 # Scan for other nodes this many seconds
}


##
## local_settings.py can be used to override environment-specific settings
## like database and email that differ between development and production.
##

try:
    #pylint: disable-msg=W0401
    from settings_local import * #IGNORE:W0614
except ImportError:
    pass


