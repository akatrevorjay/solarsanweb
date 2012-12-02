
import os
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
from ..queryset import QuerySet

from django.conf import settings
if settings.SERVER_IS_LINUX:
    from .os_linux import backend
elif settings.SERVER_IS_KFREEBSD:
    from .os_kfreebsd import backend

class DeviceQuerySet(QuerySet):
    # This will be set later after Device class is created
    _wrap_objects = None
    def _get_objs(self):
        wrapper = getattr(self, '_wrap_objects', None)
        devs = self._get_raw_objs()
        if wrapper:
            devs = [wrapper(d) for d in devs]
        return devs

    def _get_raw_objs(self):
        #return backend.get_devices()
        #return list(Drives().all())
        #return list(
        return backend.get_devices()

    def __init__(self, *args, **kwargs):
        if 'devices' in kwargs:
            kwargs['objects'] = kwargs.pop('devices')
        super(DeviceQuerySet, self).__init__(*args, **kwargs)

    def _device_check(self):
        pass



#class Device(object):
#    """Device object"""
#
#    def __init__(self, path):
#        self._parted = get_device_by_path(path)
#        self._udisks = get_device_by_path(path)
#    # TODO


#class Devices(DeviceQuerySet):
#    pass


#class Drives(DeviceQuerySet):
#    base_filter = {
#        'DeviceIsDrive': True,
#    }

#    ## TODO Drives should maybe not show volume devs?
#    #path_by_id = d.path_by_id()
#    #basepath = os.path.basename(path_by_id)
#    #if basepath.startswith('zd'):
#    #    continue


class Mirror(DeviceQuerySet):
    """Mirrored device object
    """
    _mirrorable = True

    def _zpool_args(self):
        assert len(self) % 2 == 0
        modifiers = self._zpool_create_modifiers
        return modifiers + [dev._zpool_arg() for dev in self.objects]

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
        if v in self.objects:
            raise ValueError("Cannot mirror the same device multiple times")

    def __setitem__(self, k, v):
        self._device_check(v)
        return super(Mirror, self).__setitem__(k, v)

    def append(self, v):
        self._device_check(v)
        return super(Mirror, self).append(v)

    def __add__(self, other):
        return self.append(other)


class BaseDevice(backend.BaseDevice):
    """Device object
    """
    path = None
    _mirrorable = False
    _backend_device = None
    _zpool_create_modifier = None

    def __init__(self, arg):
        if isinstance(arg, backend.RawDevice):
            self._backend_device = arg
        else:
            self._backend_device = backend.get_device_by_path(arg)
        self.path = self.path_by_id(basename=True)

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.path)

    def _zpool_arg(self):
        #assert self.is_drive or self.is_partition
        #assert not self.is_mounted
        #assert not self.is_partitioned
        return self.path_by_id()

    # TODO udisks device
    def paths_udisks(self, by_id=True, by_path=True):
        ret = set([self._backend_device.DeviceFile])
        if by_id:
            ret.update(self._backend_device.DeviceFileById)
        if by_path:
            ret.update(self._backend_device.DeviceFileByPath)
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



class __MirrorableDeviceMixin(object):
    """_mirrorable device mixin
    """
    _mirrorable = True

    def __add__(self, other):
        if isinstance(other, (self.__class__, Mirror)):
            return Mirror([self, other])


class Device(BaseDevice):
    pass


class Disk(__MirrorableDeviceMixin, BaseDevice):
    """Disk device object
    """
    pass


class Cache(__MirrorableDeviceMixin, BaseDevice):
    """Cache device object
    """
    _zpool_create_modifier = 'cache'


class Spare(BaseDevice):
    """Spare device object
    """
    _zpool_create_modifier = 'spare'


class Log(__MirrorableDeviceMixin, BaseDevice):
    """Log device object
    """
    _zpool_create_modifier = 'log'



DeviceQuerySet._wrap_objects = Device
#DeviceQuerySet._wrap_objects = backend.Device
#Devices = Devices()
#Drives = Drives()


class Devices(DeviceQuerySet):
    pass


class Drives(DeviceQuerySet):

    #base_filter={
    #    # TODO This is for udisks, what attr fits here?
    #    'DeviceIsDrive': True,
    #}

    ## TODO Drives should maybe not show volume devs?
    #path_by_id = d.path_by_id()
    #basepath = os.path.basename(path_by_id)
    #if basepath.startswith('zd'):
    #    continue

    pass



