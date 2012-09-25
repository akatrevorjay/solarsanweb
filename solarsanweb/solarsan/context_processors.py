
from django.conf import settings
from storage.models import Pool

def pools(request):
    try:
        pools = Pool.objects.all()
    except:
        pools = []

    return {'pools': pools}


def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}


