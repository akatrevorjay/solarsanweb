
from ..queryset import QuerySet
from . import Device

from django.conf import settings
if settings.SERVER_IS_LINUX:
    from .os_linux import *
    from . import os_linux as server_os
elif settings.SERVER_IS_KFREEBSD:
    from .os_kfreebsd import *
    from . import os_kfreebsd as server_os


class DeviceQuerySet(QuerySet):
    _wrap_objects = Device

    def _get_objects(self):
        wrapper = getattr(self, '_wrap_objects', None)
        devs = backend.get_devs()
        if wrapper:
            devs = [wrapper(d) for d in devs]
        return devs

    def __init__(self, *args, **kwargs):
        if 'devices' in kwargs:
            kwargs['objects'] = kwargs.pop('devices')
        super(DeviceQuerySet, self).__init__(*args, **kwargs)

    def _device_check(self):
        pass


