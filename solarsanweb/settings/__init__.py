# Django settings for solarsanweb project.

# Import base settings
from .base import *

#
# local.py can be used to override environment-specific settings
# like database and email that differ between development and production.
#

try:
    from .local import *
except ImportError:
    pass

#
# Import app-specific settings
#

for app in PROJECT_APPS:
    try:
        app_module = __import__(app, globals(), locals(), ["settings"])
        app_settings = getattr(app_module, "settings", None)
        for setting in dir(app_settings):
            if setting == setting.upper():
                locals()[setting] = getattr(app_settings, setting)
    except ImportError:
        pass

#
# Monkey patch storage classes.
#   (Yes, I'm aware how bad of a location for this this is.)
#

import storage.patch
storage.patch.patch_queryset()
storage.patch.patch_rtslib()
