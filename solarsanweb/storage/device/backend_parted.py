
#import os
import parted
from .queryset import DeviceQuerySet


def get_device_by_path(device):
    """Returns parted device for given device file
    """
    dev = parted.getDevice(device)
    dsk = parted.Disk(dev)
    return dsk


def get_devices(path):
    """Enumerates parted devies"""
    return parted.getAllDevices()


class Device(object):
    def __init__(self, path):
        self._parted = get_device_by_path(path)


class BaseQuerySet(DeviceQuerySet):
    def _get_objects(self):
        return get_devices()


class Devices(BaseQuerySet):
    pass


class Drives(BaseQuerySet):
    base_filter={
        # TODO This is for udisks, what attr fits here?
        'DeviceIsDrive': True,
    }
