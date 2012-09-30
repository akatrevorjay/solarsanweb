

from solarsan.utils import FormattedException, LoggedException
import rtslib
from storage.models import Pool, Filesystem, Volume, Snapshot


root = rtslib.RTSRoot()


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


def list(fabric_module=None, ret_type=None):
    if fabric_module:
        fabric_module = get_fabric_module(fabric_module)
        ret = fabric_module.targets
    else:
        ret = root.targets

    if ret_type == dict:
        ret = group_by(ret, 'wwn')
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
        targets = get_targets()
        if wwn in targets:
            return targets[wwn]
        else:
            raise FormattedException("Target with wwn=%s does not exist", wwn)


def create_target(self, fabric_module, wwn=None):
    fabric_module = get_fabric_module(fabric_module)
    return rtslib.Target(fabric_module, wwn=wwn, mode='create')




