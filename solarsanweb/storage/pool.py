
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

        create('dpool',
            Mirror(Disk('sda'), Disk('sdb')),
            Disk('sda') + Disk('sdb'),
            Log('sda') + Log('sdb'),
            Cache('sde'),
            Cache('sdf'),
            )

        """
        cmd = sh.zpool.bake('create', self.name)

        args = []
        for dev in devices:
            if getattr(dev, '_zpool_create_args'):
                args.extend(dev._zpool_create_args())
            else:
                args.append(dev._zpool_create_arg())

        # TODO Retval check, pool check, force a Zfs import scan in bg
        #try:
        rv = cmd(*args)
        #except rv.ErrorReturnCode_1:
        #    return False
        return True

    def add(pool, device):
        """Grow pool by adding new device.

        add('dpool',
            {'mirror': ['sdf', 'sdg']},
            )

        """
        pass

    def remove(pool, device):
        """Removes device from pool.

        remove('dpool', 'sdc')

        """
        pass

    def attach(pool, device, new_device):
        """Attaches new device to existing device, creating a device mirror.

        attach('dpool', 'sdb', 'sdc')

        """
        pass

    def detach(pool, device):
        """Detaches existing device from an existing device mirror.

        detach('dpool', 'sdb')

        """
        pass
