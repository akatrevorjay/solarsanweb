
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
