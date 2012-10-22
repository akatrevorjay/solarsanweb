
#import logging
import sh
#from collections import defaultdict
#import storage.device


class _BaseDataset(object):
    def __init__(self, name):
        self.name = name

    # Good candidates to share code once again:
    #def exists
    #def destroy


class Filesystem(_BaseDataset):
    def exists(self):
        """Checks if filesystem exists.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.exists()

        """
        try:
            sh.zfs('list', '-t', 'filesystem', self.name)
        except sh.ErrorReturnCode_1:
            return False
        return True

    def create(self):
        """Creates storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.create()

        """
        try:
            sh.zfs('create', self.name)
        except sh.ErrorReturnCode_1:
            # I'm not sure about this; the problem is if it creates the
            # dataset, but fails to mount it for some reason, we're left with
            # the pieces and a simple 1 retval...
            #if self.exists():
            #    self.destroy()
            raise

        # TODO Force scan of this in bg
        return True

    def destroy(self):
        """destroys storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.destroy()

        """
        sh.zfs('destroy', self.name)
        # TODO Force delete of this in bg
        return True


class Volume(_BaseDataset):
    def exists(self):
        """Checks if volume exists.

        volume = Volume('dpool/tmp/test0')
        volume.exists()

        """
        try:
            sh.zfs('list', '-t', 'volume', self.name)
        except sh.ErrorReturnCode_1:
            return False
        # TODO Force scan of this in bg
        return True

    def create(self, size):
        """Creates storage volume.

        volume = Volume('dpool/tmp/test0')
        volume.create()

        """
        # TODO Check size to make sure it's decent.

        try:
            # -V volume, -s sparse, -b blocksize, -o prop=val
            # -p works like mkdir -p, creates non-existing parent datasets.
            sh.zfs('create', '-V', size, self.name)
        except sh.ErrorReturnCode_1:
            # I'm not sure about this; the problem is if it creates the
            # dataset, but fails to mount it for some reason, we're left with
            # the pieces and a simple 1 retval...
            #if self.exists():
            #    self.destroy()
            raise
        # TODO Force scan of this in bg
        return True

    def destroy(self):
        """destroys storage volume.

        volume = Volume('dpool/tmp/test0')
        volume.destroy()

        """
        sh.zfs('destroy', self.name)
        # TODO Force delete of this in bg
        return True
