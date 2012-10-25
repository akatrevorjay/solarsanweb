
import logging
import sh
#from collections import defaultdict
#import storage.device


class Pool(object):
    """Storage Pool object
    """

    class Properties(object):
        """Storage Pool Properties object
        """

        class Property(object):
            """Storage Pool Property object
            """
            name = None
            value = None
            source = None

            def __str__(self):
                return self.value

            def __unicode__(self):
                return self.value

            def __repr__(self):
                return '<Property(name=%s, value=%s, source=%s)>' % (self.name, self.value, self.source)

        def __init__(self, parent):
            self.parent = parent

        def __getitem__(self, k):
            pass
            #ret = self.Property()
            #return ret

        def __setitem__(self, k, v):
            pass

        def __iter__(self):
            pass

    name = None

    def __init__(self, name):
        self.name = name
        self.properties = self.Properties(self)

    def exists(self):
        """Checks if pool exists.

        pool = Pool('dpool')
        pool.exists()

        """
        try:
            sh.zpool('list', self.name)
        except sh.ErrorReturnCode_1:
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

    def destroy(self, confirm=False):
        """Destroys storage pool.

        pool = Pool('dpool')
        pool.destroy()

        """
        if not confirm:
            raise Exception('Destroy of storage pool requires confirm=True')
        sh.zpool('destroy', self.name)
        return True

    def add(self, device):
        """Grow pool by adding new device.

        pool = Pool('dpool')
        pool.add(
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
        pool.remove(Disk('sdc'))

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
        pool.attach(Disk('sdb'), Disk('sdc'))

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
        pool.detach('sdb')

        """
        cmd = sh.zpool.bake('detach', self.name)

        args = []
        for dev in [device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def status(self):
        raise NotImplementedError

    def iostat(self):
        raise NotImplementedError
