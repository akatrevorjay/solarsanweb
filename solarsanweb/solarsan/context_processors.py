
from django_mongokit import get_database, connection
from storage.models import zPool

def pools(request):
    try:
        conn = get_database()[zPool.collection_name]
        pools = conn.zPool.find()
        #pools = Pool.objects.all()
        return {'pools': pools}
    except:
        return {}

