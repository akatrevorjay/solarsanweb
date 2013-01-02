
##
## Production
##

import os
from solarsanweb.paths import PROJECT_NAME, TOP_DIR, PROJECT_DIR, DATA_DIR

#DEBUG = TEMPLATE_DEBUG = False
#SECRET_KEY = 'thoothooj1yapee9ohPooqua6le3eej5lairuxeer6thoaveid0oocaufohneiw1'

DATABASES = {
    # TODO If MongoDB is the method moving forward, then this may want to be
    # changed to sqlite for non-compat apps, then use a DatabaseRouter to
    # selectively route queries to the proper db.
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',   # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(DATA_DIR, '%s.sqlite3' % PROJECT_NAME),                   # Or path to database file if using sqlite3.
        #'USER': 'root',                         # Not used with sqlite3.
        #'PASSWORD': 'locsol',                   # Not used with sqlite3.
        #'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
        #'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
    },
}

## HTTPS only
#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True


