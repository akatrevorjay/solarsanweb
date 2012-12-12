
from solarsan.utils import FormattedException, LoggedException
from storage.models import Pool, Filesystem, Volume, Snapshot
#from django.core.cache import cache
from django.conf import settings

if settings.SERVER_IS_LINUX:
    import rtslib
    root = rtslib.RTSRoot()
elif settings.SERVER_IS_KFREEBSD:
    class FakeRoot(object):
        targets = []
    root = FakeRoot()


class DoesNotExist(FormattedException):
    pass


def group_by(iterable, group_by):
    ret = {}
    for i in iterable:
        key = getattr(i, group_by)
        ret[key] = i
    return ret


def get_fabric_module(name):
    if not isinstance(name, rtslib.FabricModule):
        name = rtslib.FabricModule(name)
    return name


import storage.cache


def target_list(ret_type=None, shorten=False, cached=False):
    ret = None
    if cached:
        ret = storage.cache.targets()
    if not cached or not ret:
        ret = [x for x in root.targets]

    if ret_type == dict:
        ret = group_by(ret, 'wwn')
        if shorten:
            update = {}
            for k, v in ret.iteritems():
                update[short_wwn(k)] = v
            #ret.update(update)
            ret = update

    elif ret_type == list:
        retn = []
        for t in root.targets:
            retn.append(t)
        ret = retn

    return ret


def get(wwn, fabric_module=None, cached=False):
    if fabric_module:
        fabric_module = get_fabric_module(fabric_module)
        return rtslib.Target(fabric_module, wwn=wwn, mode='lookup')
    else:
        targets = target_list(cached=cached)
        for target in targets:
            if target.wwn == wwn:
                return target
        else:
            raise DoesNotExist("Target with wwn=%s does not exist", wwn)


def create_target(fabric_module, wwn=None):
    fabric_module = get_fabric_module(fabric_module)
    ret = rtslib.Target(fabric_module, wwn=wwn, mode='create')
    # Create new targets cache
    storage.cache.targets(force=True)
    return ret


def get_sessions():
    return list(root.sessions)


def get_tpg(target, tag, fabric_module=None):
    if isinstance(target, basestring):
        target = get(target, fabric_module)
    if not isinstance(target, rtslib.Target):
        raise LoggedException("Got a target that wasn't a rtslib.Target instance: '%s'", target)
    return target.get_tpg(tag)


def storage_object_list():
    return list(root.storage_objects)


def get_storage_objects(name=None, path=None, max=None):
    ret = []
    for so in storage_object_list():
        if name and so.name != name:
            continue
        if path and so.path != path:
            continue
        ret.append(so)
    if max and len(ret) > max:
        raise LoggedException("For some reason, multiple storage objects matched your expression: {name=%s, path=%s}", name, path)
    return ret


def get_storage_object(**kwargs):
    kwargs['max'] = 1
    return get_storage_objects(**kwargs)[0]


def is_tpg_lun_available(tpg, i):
    for lun in tpg.luns:
        if lun.lun == i:
            return False
    return True


def get_tpg_available_lun(tpg):
    for i in xrange(0, 100):
        if is_tpg_lun_available(tpg, i):
            return i


def get_or_create_bso(name, dev=None):
    try:
        ret = rtslib.BlockStorageObject(name)
        if ret.udev_path != dev:
            ret.udev_path = dev
    except rtslib.RTSLibNotInCFS:
        if rtslib.utils.is_dev_in_use(dev):
            print "device is in use"
            return
        ret = rtslib.BlockStorageObject(name, dev=dev)
    return ret


def get_or_create_bso_lun_in_tpg(bso, tpg):
    for lun in tpg.luns:
        if lun.storage_object == bso:
            return lun
    return rtslib.LUN(tpg, storage_object=bso)
