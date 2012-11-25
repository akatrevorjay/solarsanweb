
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
        ret = None
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

    def __init__(self, devices=None, base_filter=None, base_filter_replace=False):
        if devices:
            self._devices = devices
        if base_filter:
            if base_filter_replace:
                self._base_filter = base_filter
            else:
                if not self._base_filter:
                    self._base_filter = {}
                self._base_filter.update(base_filter)

    def all(self):
        return self.filter()

    def filter(self, **kwargs):
        if self._base_filter:
            kwargs.update(self._base_filter)
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


#class _Devices(_QuerySet):
#    pass


#class _Drives(_QuerySet):
#    _base_filter = {'is_drive': True}


Devices = _QuerySet()


## TODO Drives should maybe not show volume devs?
#path_by_id = d.path_by_id()
#basepath = os.path.basename(path_by_id)
#if basepath.startswith('zd'):
#    continue

Drives = _QuerySet(
    base_filter={
        'is_drive': True,
    },
)


class Mirror(_QuerySet):
    """Mirrored device object
    """
    _mirrorable = True

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
        return self.append(other)


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
        paths = self.paths()
        ret = None

        path_by_uuid = None
        path_by_path = None
        path_by_id = None
        path_short = None
        for x, path in enumerate(paths):
            if path.startswith('/dev/disk/by-uuid/'):
                path_by_uuid = path
            elif path.startswith('/dev/disk/by-path/'):
                path_by_path = path
            elif path.startswith('/dev/disk/by-id/'):
                path_by_id = path
            if not path_short or len(path_short) > len(path):
                path_short = path

        for i in [path_by_uuid, path_by_id, path_short, path_by_path, paths[0]]:
            if i:
                ret = i
                break

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


class __MirrorableDeviceMixin(object):
    """_mirrorable device mixin
    """
    _mirrorable = True

    def __add__(self, other):
        if isinstance(other, (self.__class__, Mirror)):
            return Mirror([self, other])


class Device(_BaseDevice):
    pass


class Disk(__MirrorableDeviceMixin, _BaseDevice):
    """Disk device object
    """
    pass


class Cache(__MirrorableDeviceMixin, _BaseDevice):
    """Cache device object
    """
    _zpool_create_modifier = 'cache'


class Spare(_BaseDevice):
    """Spare device object
    """
    _zpool_create_modifier = 'spare'


class Log(__MirrorableDeviceMixin, _BaseDevice):
    """Log device object
    """
    _zpool_create_modifier = 'log'
