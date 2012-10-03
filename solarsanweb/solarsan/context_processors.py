from django.conf import settings

def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}
