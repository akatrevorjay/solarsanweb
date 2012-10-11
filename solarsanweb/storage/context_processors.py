
import storage.cache


def storage_objects(request):
    ret = storage.cache.storage_objects(request)
    ret['fabrics'] = {'iscsi': 'iSCSI'}
    return ret

