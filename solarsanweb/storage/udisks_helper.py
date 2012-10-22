
import os
import udisks


_udisks = udisks.UDisks()


def filter_by_attrs(args, **kwargs):
    """Takes a list of objects and returns only those where each **kwargs
    matches the attributes exactly.
    """
    if not kwargs:
        return args
    ret = []
    add_arg = True
    for arg in args:
        for attr, attr_vals in kwargs.items():
            if not isinstance(attr_vals, list):
                attr_vals = [attr_vals]

            #logging.debug("arg=%s getattr=%s attr=%s attr_vals=%s", arg,
            #              getattr(arg, attr), attr, attr_vals)
            if getattr(arg, attr) not in attr_vals:
                add_arg = False
                break
        #logging.debug("add_arg=%s", add_arg)
        if add_arg:
            ret.append(arg)
        else:
            add_arg = True
    return ret

    #return [arg for arg in args if
    #        all(
    #            [getattr(arg, k) == v for k, v in kwargs.items()]
    #        )]


def get_devs(**kwargs):
    """Enumerates udisk devices
    """
    return filter_by_attrs(_udisks.EnumerateDevices(),
                           **kwargs)


def get_drives(**kwargs):
    """Enumerates udisk drive devices
    """
    kwargs['DeviceIsDrive'] = True
    return get_devs(**kwargs)


def get_device_by_path(device):
    """Returns udisk device for given device file
    """
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


