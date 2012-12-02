from django.conf import settings
if not settings.SERVER_IS_LINUX:
    raise ImportError('UDisks can only be used on Linux')

#import os
import udisks
_udisks = udisks.UDisks()


def get_device_by_path(path):
    """Returns udisks device for given device path"""
    dbus_obj = _udisks.iface.FindDeviceByDeviceFile(path)
    if dbus_obj:
        return udisks.device.Device(dbus_obj)


def get_devices():
    """Enumerates udisks devices"""
    return _udisks.EnumerateDevices()



