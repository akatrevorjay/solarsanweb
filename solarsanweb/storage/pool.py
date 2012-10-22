
#import logging
import sh
#from collections import defaultdict
#import storage.device


class Pool(object):
    def __init__(self, name):
        self.name = name

    def exists(self):
        try:
            rv = sh.zpool('list', self.name)
        except rv.ErrorReturnCode_1:
            return False
        return True

    def create(self, *devices):
        """Creates storage pool.

        pool = Pool('dpool')
        pool.create(Mirror(Disk('sda'), Disk('sdb')),
            Disk('sda') + Disk('sdb'),
            Log('sda') + Log('sdb'),
            Cache('sde'),
            Cache('sdf'),
            )

        """
        cmd = sh.zpool.bake('create', self.name)

        args = []
        for dev in devices:
            if getattr(dev, '_zpool_args'):
                args.extend(dev._zpool_args())
            else:
                args.append(dev._zpool_arg())

        # TODO Retval check, pool check, force a Zfs import scan in bg
        #try:
        cmd(*args)
        #except rv.ErrorReturnCode_1:
        #    return False
        return True

    def add(self, device):
        """Grow pool by adding new device.

        pool = Pool('dpool')
        pool.add('dpool',
            Disk('sda') + Disk('sdb'),
            )

        """
        cmd = sh.zpool.bake('add', self.name)

        args = []
        for dev in [device]:
            if getattr(dev, '_zpool_args'):
                args.extend(dev._zpool_args())
            else:
                args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def remove(self, device):
        """Removes device from pool.

        pool = Pool('dpool')
        pool.remove('dpool', Disk('sdc'))

        """
        cmd = sh.zpool.bake('remove', self.name)

        args = []
        for dev in [device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def attach(self, device, new_device):
        """Attaches new device to existing device, creating a device mirror.

        pool = Pool('dpool')
        pool.attach('dpool', Disk('sdb'), Disk('sdc'))

        """
        cmd = sh.zpool.bake('attach', self.name)

        args = []
        for dev in [device, new_device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def detach(self, device):
        """Detaches existing device from an existing device mirror.

        pool = Pool('dpool')
        pool.detach('dpool', 'sdb')

        """
        cmd = sh.zpool.bake('detach', self.name)

        args = []
        for dev in [device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True
