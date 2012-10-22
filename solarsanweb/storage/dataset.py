
#import logging
import sh
#from collections import defaultdict
#import storage.device


class _BaseDataset(object):
    def __init__(self, name):
        self.name = name

    def exists(self):
        """Checks if dataset exists.

        dataset = _BaseDataset('dpool/tmp/test0')
        dataset.exists()

        """
        try:
            sh.zfs('list', self.name)
        except sh.ErrorReturnCode_1:
            return False
        return True


class Filesystem(_BaseDataset):
    def create(self):
        """Creates storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.create()

        """
        try:
            sh.zfs('create', self.name)
        except sh.ErrorReturnCode_1:
            if self.exists():
                self.destroy()
            raise
        return True

    def destroy(self):
        """destroys storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.destroy()

        """
        sh.zfs('destroy', self.name)
        return True
