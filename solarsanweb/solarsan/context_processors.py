
from storage.models import Pool

def pools(request):
    try:
        pools = Pool.objects.all()
        return {'pools': pools}
    except:
        return {}

