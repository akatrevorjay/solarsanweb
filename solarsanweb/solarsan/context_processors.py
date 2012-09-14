
from django.conf import settings
import zfs as z


def pools(request):
    try:
        pools = z.Pool.dbm.objects.values_list('name')
        pools = [z.Pool(x) for x in pools]
    except:
        pools = []

    return {'pools': pools}


def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}


