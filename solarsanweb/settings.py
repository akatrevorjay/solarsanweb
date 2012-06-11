# Django settings for solarsanweb project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Trevor Joynson', 'trevorj@localhostsolutions.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'solarsanweb',                      # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': 'locsol',                  # Not used with sqlite3.
        'HOST': 'db.solarsan.local',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

PROJECT_NAME = "solarsanweb"

## Paths
import os, sys

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PROJECT_DIR = os.path.join(TOP_DIR, PROJECT_NAME)
DATA_DIR = os.path.join(TOP_DIR, "data")

for i in ['vendor', 'vendor-local']:
    sys.path.insert(0, os.path.join(TOP_DIR, i))

sys.path.insert(0, os.path.join(PROJECT_DIR, 'lib'))
sys.path.insert(0, PROJECT_DIR)


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
USE_I18N = False

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jk$cr7u4$8@oj&u+n8&h*h_*g3j8@e3i&pm5k!@h77a8@#j@na'

#TEMPLATE_CONTEXT_PROCESSORS = (
#    # default template context processors
#    'django.core.context_processors.auth',
#    'django.core.context_processors.debug',
#    'django.core.context_processors.i18n',
#    'django.core.context_processors.media',
#
#    # django 1.2 only
#    'django.contrib.messages.context_processors.messages',
#
#    # required by django-admin-tools
#    'django.core.context_processors.request',
#)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
#    ('django.template.loaders.cached.Loader', (
        'jingo.Loader',
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        'django.template.loaders.eggs.Loader',
#    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

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
)

#def custom_show_toolbar(request):
#    return True # Always show toolbar, for example purposes only.

INTERNAL_IPS=['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    #'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    'TAG': 'div',
    'ENABLE_STACKTRACES' : True,
}


ROOT_URLCONF = PROJECT_NAME + '.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = PROJECT_NAME + '.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates"),
)

ADMINTOOLS_BOOTSTRAP_SITE_LINK = '/'

INSTALLED_APPS = (
    'bootstrap',
#    'admin_tools',
#    'admin_tools.theming',
#    'admin_tools.menu',
#    'admin_tools.dashboard',
#    'admintools_bootstrap',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',

    # Libs
    'djcelery',
    'kombu.transport.django',
    #'debug_toolbar',
    'django_extensions',
    'djsupervisor',
    'south',

    # Apps
    'solarsan',
    #'bootstrap_example.root',
)

# Cache backends
CACHES = {
    'default_mem': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': PROJECT_NAME,
    },
    'default_db': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': PROJECT_NAME+'_django_db_cache',
    }
}
CACHES['default'] = CACHES['default_mem']

# Persistent sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
#SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# HTTPS only
SESSION_COOKIE_SECURE = True

# Jinja2 env config
JINJA_CONFIG = {
    'auto_reload': True,
    'extensions': ['jinja2.ext.i18n', 'jinja2.ext.with_', 'jinja2.ext.loopcontrols'],
}

# List of apps that do not use Jingo
JINGO_EXCLUDE_APPS = ('admin', 'registration', 'debug_toolbar')

## Celery
# django-celery
import djcelery
djcelery.setup_loader()
# celery
BROKER_URL = "amqp://guest:guest@localhost:5672//"
#BROKER_USE_SSL = True
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = (
    "solarsan.tasks.graphs",
    "solarsan.tasks.stats",
    "solarsan.tasks.auto_snapshot",
    "solarsan.tasks.locsol_backup",
    "solarsan.tasks.import_zfs_metadata",
    "solarsan.tasks.cluster",
    "solarsan.tasks",
)
#CELERY_DEFAULT_RATE_LIMIT = "100/s"
if DEBUG:
    CELERY_SEND_EVENTS = True
    CELERY_SEND_TASK_SENT_EVENT = True
## queues=[cluster, default]
#CELERY_QUEUES
#CELERY_ROUTES = ({"myapp.tasks.compress_video": {
#                        "queue": "video",
#                        "routing_key": "video.compress"
#                 }}, )
#CELERY_DEFAULT_QUEUE
#CELERY_CREATE_MISSING_QUEUES
#CELERY_DEFAULT_ROUTING_KEY

#CELERY_RESULT_BACKEND = "mongodb"
#CELERY_MONGODB_BACKEND_SETTINGS = {
    #"host": "127.0.0.1",
    #"port": 27017,
    #"database": "celery",
    #"taskmeta_collection": "my_taskmeta" # Collection name to use for task output
#}
#BROKER_BACKEND = "mongodb"
#BROKER_HOST = "localhost"
#BROKER_PORT = 27017
#BROKER_USER = ""
#BROKER_PASSWORD = ""
#BROKER_VHOST = "celery"

CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

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

# Set your DSN value
SENTRY_DSN = 'http://7774c7fd239647f290af254c36d6153c:796e31c848d74c4b9f9fab04abdf62a5@sentry.solarsan.local/2'

# Add raven to the list of installed apps
INSTALLED_APPS = INSTALLED_APPS + (
        'raven.contrib.django',
        )
MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
        # Catch 404s
        'raven.contrib.django.middleware.Sentry404CatchMiddleware',
        'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
        )


