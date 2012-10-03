

from solarsan.utils import FormattedException, LoggedException
import rtslib
import rtslib.tcm
from storage.models import Pool, Filesystem, Volume, Snapshot

from django.core.cache import cache
from django.conf import settings

root = rtslib.RTSRoot()


CACHE_TIMEOUT = 600



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


def list(ret_type=None, shorten=False, cached=False):
    ret = None
    if cached:
        ret = cache.get('targets')
    if not cache or not ret:
        ret = [x for x in root.targets]
        if cached:
            cache.set('targets', ret, CACHE_TIMEOUT)
    #else:
    #    # Currently no cache for this as this isn't used at all atm.
    #    fabric_module = get_fabric_module(fabric_module)
    #    ret = fabric_module.targets

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

def get_target(wwn, fabric_module=None):
    if fabric_module:
        fabric_module = get_fabric_module(fabric_module)
        return rtslib.Target(fabric_module, wwn=wwn, mode='lookup')
    else:
        targets = list()
        if wwn in targets:
            return targets[wwn]
        else:
            raise FormattedException("Target with wwn=%s does not exist", wwn)


def create_target(self, fabric_module, wwn=None):
    fabric_module = get_fabric_module(fabric_module)
    return rtslib.Target(fabric_module, wwn=wwn, mode='create')




