
from django.conf import settings
from storage.models import Pool, Filesystem, Volume


def pools(request):
    r = {}
    try:
        r = {'pools': Pool.objects.all(),
             'filesystems': Filesystem.objects.all(),
             'volumes': Volume.objects.all(),
             }
    except:
        r = {'pools': [],
             'filesystems': [],
             'volumes': [],
             }
    return r


def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}


