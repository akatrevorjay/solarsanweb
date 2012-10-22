
import os
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
from storage.udisks_helper import get_device_by_path, get_devs, get_drives, filter_by_attrs
import udisks
from copy import copy


class _QuerySet(object):
    """QuerySet for device objects
    """
    _base_filter = None
    _lazy = None
    _devices = None

    @property
    def devices(self):
        if isinstance(self._devices, list):
            ret = copy(self._devices)
        if not ret:
            ret = self._get_devices()
        return ret

    def _get_devices(self):
        devices = [Device(drive) for drive in get_devs()]
        if isinstance(self._devices, list):
            self._devices = devices
        return devices

    def __init__(self, devices=None):
        if devices:
            self._devices = devices

    def all(self):
        return self.devices

    def filter(self, **kwargs):
        base_filter = self._base_filter
        if base_filter:
            kwargs.update(self.base_filter)
        return filter_by_attrs(self, **kwargs)

    def _device_check(self):
        pass

    def __setitem__(self, k, v):
        self.devices[k] = v

    def append(self, v):
        self.devices.append(v)

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.devices.__repr__())

    def __len__(self):
        return len(self.devices)

    def __getitem__(self, key):
        return self.devices[key]

    def __delitem__(self, key):
        del self.devices[key]

    def __iter__(self):
        return iter(self.devices)

    def __reversed__(self):
        return reversed(self.devices)


class Drives(_QuerySet):
    _base_filter = {'is_drive': True}


class Mirror(_QuerySet):
    """Mirrored device object
    """
    _mirrorable = True

    def __init__(self, devices=None):
        self.devices = []
        for dev in devices:
            self.append(dev)

    def _zpool_args(self):
        assert len(self) % 2 == 0
        modifiers = self._zpool_create_modifiers
        return modifiers + [dev._zpool_arg() for dev in self.devices]

    @property
    def _zpool_create_modifiers(self):
        ret = []
        device_class = self._device_class
        if device_class:
            #ret.extend(device_class._zpool_create_modifiers)
            modifier = device_class._zpool_create_modifier
            if modifier:
                ret.append(modifier)
        ret.append('mirror')
        return ret

    @property
    def _device_class(self):
        if self:
            return self[0].__class__

    def _device_check(self, v):
        device_class = self._device_class
        if not device_class:
            return
        if not v.__class__ == device_class:
            raise ValueError("Cannot mirror different types of devices")
        if v in self.devices:
            raise ValueError("Cannot mirror the same device multiple times")

    def __setitem__(self, k, v):
        self._device_check(v)
        return super(Mirror, self).__setitem__(k, v)

    def append(self, v):
        self._device_check(v)
        return super(Mirror, self).append(v)

    def __add__(self, other):
        if not other._mirrorable:
            raise ValueError
        if isinstance(other, self.__class__):
            return self.__class__(self + other)
        else:
            return self.__class__(self + [other])


class _BaseDevice(object):
    """Device object
    """
    path = None
    _mirrorable = False
    _udisk_device = None
    _zpool_create_modifier = None

    def __init__(self, arg):
        if isinstance(arg, udisks.device.Device):
            self._udisk_device = arg
        else:
            self._udisk_device = get_device_by_path(arg)
        self.path = self.path_by_id(basename=True)

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.path)

    def _zpool_arg(self):
        #assert self.is_drive or self.is_partition
        #assert not self.is_mounted
        #assert not self.is_partitioned
        return self.path_by_id()

    """
    Device Info
    """

    # Vendor is apparently 'ATA' ? Doesn't make sense, not including this for
    # now. If needed just split(self.model)[0].
    #@property
    #def vendor(self):
    #    return self._udisk_device.DriveVendor

    @property
    def model(self):
        return self._udisk_device.DriveModel

    @property
    def revision(self):
        return self._udisk_device.DriveRevision

    @property
    def serial(self):
        return self._udisk_device.DriveSerial

    # Partitions only
    #@property
    #def uuid(self):
    #    return self._udisk_device.DriveUuid

    @property
    def wwn(self):
        return self._udisk_device.DriveWwn

    def size(self, human=False):
        ret = self._udisk_device.DeviceSize
        if human:
            ret = convert_bytes_to_human(ret)
        return ret

    @property
    def block_size(self):
        return self._udisk_device.DeviceBlockSize

    def paths(self, by_id=True, by_path=True):
        ret = set([self._udisk_device.DeviceFile])
        if by_id:
            ret.update(self._udisk_device.DeviceFileById)
        if by_path:
            ret.update(self._udisk_device.DeviceFileByPath)
        return list(ret)

    def path_by_id(self, basename=False):
        ret = None

        paths = self.paths()
        for path in paths:
            if os.path.basename(path).startswith('scsi'):
                ret = path
                break
        if not ret:
            ret = paths[0]

        if basename:
            ret = os.path.basename(ret)
        return ret

    """
    SMART
    """

    @property
    def smart_status(self):
        return self._udisk_device.DriveAtaSmartStatus

    @property
    def is_smart_available(self):
        return self._udisk_device.DriveAtaSmartIsAvailable

    # Not yet implemented in udisks OR in python-udisks
    #def smart_self_test(self):
    #    return self._udisk_device.DriveAtaInitiateSelfTest()

    """
    Device Properties
    """

    @property
    def is_rotational(self):
        return self._udisk_device.DriveIsRotational

    @property
    def is_partitioned(self):
        return self._udisk_device.DeviceIsPartitionTable

    @property
    def is_mounted(self):
        return self._udisk_device.DeviceIsMounted

    @property
    def mount_paths(self):
        return self._udisk_device.DeviceMountPaths

    @property
    def is_removable(self):
        return self._udisk_device.DeviceIsRemovable

    @property
    def is_readonly(self):
        return self._udisk_device.DeviceIsReadOnly

    """
    Hmm, not sure if these even belong here
    """

    @property
    def is_drive(self):
        return self._udisk_device.DeviceIsDrive

    @property
    def is_partition(self):
        return self._udisk_device.DeviceIsPartition

    """
    LVM2
    """

    @property
    def is_lvm2_lv(self):
        return self._udisk_device.DeviceIsLinuxLvm2LV

    @property
    def is_lvm2_pv(self):
        return self._udisk_device.DeviceIsLinuxLvm2PV

    """
    mdraid
    """

    @property
    def is_mdraid(self):
        return self._udisk_device.DeviceIsLinuxMd

    @property
    def is_mdraid_degraded(self):
        return self._udisk_device.LinuxMdIsDegraded

    @property
    def is_mdraid_component(self):
        return self._udisk_device.DeviceIsLinuxMdComponent


class __mirrorableDeviceMixin(object):
    """_mirrorable device mixin
    """
    _mirrorable = True

    def __add__(self, other):
        if isinstance(other, (self.__class__, Mirror)):
            return Mirror([self, other])


class Device(object):
    pass


class Disk(__mirrorableDeviceMixin, _BaseDevice):
    """Disk device object
    """
    pass


class Cache(__mirrorableDeviceMixin, _BaseDevice):
    """Cache device object
    """
    _zpool_create_modifier = 'cache'


class Spare(_BaseDevice):
    """Spare device object
    """
    _zpool_create_modifier = 'spare'


class Log(__mirrorableDeviceMixin, _BaseDevice):
    """Log device object
    """
    _zpool_create_modifier = 'log'
