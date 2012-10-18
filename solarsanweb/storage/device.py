
import os
import udisks


_udisks = udisks.UDisks()


def filter_by_attrs(args, **kwargs):
    if not kwargs:
        return args
    return [arg for arg in args if
            all(
                [getattr(arg, k) == v for k, v in kwargs.items()]
            )]


def get_devs(**kwargs):
    return filter_by_attrs(_udisks.EnumerateDevices(),
                           **kwargs)


def get_drives(**kwargs):
    kwargs['DeviceIsDrive'] = True
    return get_devs(**kwargs)


def get_device_by_path(device):
    # Cause I'm paranoid
    device_name = os.path.basename(device)
    for path in ['/dev/disk/by-id', '/dev']:
        path = os.path.join(path, device_name)
        # TODO Don't just check for existence, but be smart about what names to
        # aloow/deny. Also make sure is dev, not file.
        if os.path.exists(path):
            device_path = path
            break

    if not device_path:
        raise Exception("Could not find device '%s'" % device)

    dbus_obj = _udisks.iface.FindDeviceByDeviceFile(device_path)
    if dbus_obj:
        return udisks.device.Device(dbus_obj)


class Mirror(object):
    """Mirrored device object
    """
    __BaseDevice = None
    _mirrorable = True

    def _zpool_create_args(self):
        assert len(self) % 2 == 0
        modifiers = self._zpool_create_modifiers
        return modifiers + [dev._zpool_create_arg() for dev in self.devices]

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
        self.devices[k] = v

    def append(self, v):
        self._device_check(v)
        self.devices.append(v)

    def __add__(self, other):
        if not other._mirrorable:
            raise ValueError
        if isinstance(other, self.__class__):
            return self.__class__(self + other)
        else:
            return self.__class__(self + [other])

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.devices.__repr__())

    def __init__(self, devices=None):
        self.devices = []
        for dev in devices:
            self.append(dev)

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


class _BaseDevice(object):
    """Device object
    """
    path = None
    _mirrorable = False
    _udisk_device = None
    _zpool_create_modifier = None

    def __init__(self, path):
        self.path = path
        self._udisk_device = get_device_by_path(path)

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.path)

    def _zpool_create_arg(self):
        #assert self.is_drive or self.is_partition
        #assert not self.is_mounted
        #assert not self.is_partitioned
        return self.path

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

    @property
    def size(self):
        return self._udisk_device.DeviceSize

    @property
    def block_size(self):
        return self._udisk_device.DeviceBlockSize

    @property
    def paths_by_id(self):
        return self._udisk_device.DeviceFileById

    @property
    def path_by_id(self):
        # TODO This WILL break and is a hack, just loop through looking for the
        # best one, not like it really matters anyway, they all go to the same
        # end result...
        return self.paths_by_id[1]

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


Mirror.__BaseDevice = _BaseDevice


class __mirrorableDeviceMixin(object):
    """_mirrorable device mixin
    """
    _mirrorable = True

    def __add__(self, other):
        if isinstance(other, (self.__class__, Mirror)):
            return Mirror([self, other])


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
