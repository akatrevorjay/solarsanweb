
from django.conf import settings
if not settings.SERVER_IS_LINUX:
    raise ImportError('UDisks can only be used on Linux')

import os
import udisks
_udisks = udisks.UDisks()
from .queryset import DeviceQuerySet


def get_device_by_path(path):
    """Returns udisks device for given device path"""
    dbus_obj = _udisks.iface.FindDeviceByDeviceFile(path)
    if dbus_obj:
        return udisks.device.Device(dbus_obj)


def get_devices():
    """Enumerates udisks devices"""
    return _udisks.EnumerateDevices()


class Device(object):
    def __init__(self, path):
        self._udisks = get_device_by_path(path)


class BaseQuerySet(DeviceQuerySet):
    def _get_objects(self):
        return get_devices()


class Devices(BaseQuerySet):
    pass


class Drives(BaseQuerySet):
    base_filter={
        'DeviceIsDrive': True,
    }
