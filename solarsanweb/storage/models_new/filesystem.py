
#import mongoengine as m

#import zfs
#import zfs.cmd
import zfs.objects

#from .pool import Pool
#from .filesystem import Filesystem
#from .volume import Volume

from . import zfsBase
from .dataset import DatasetDocument, DatasetBase, SnapshottableDatasetBase


class FilesystemDocument(DatasetDocument):
    #meta = {'abstract': True,}
    pass


class FilesystemBase(zfs.objects.FilesystemBase):
    pass


class Filesystem(FilesystemDocument, FilesystemBase, SnapshottableDatasetBase, DatasetBase, zfsBase):
#class Filesystem(FilesystemBase, SnapshottableDatasetBase, DatasetBase, zfsBase, FilesystemDocument):
    pass


#class Filesystem(FilesystemDocument, SnapshottableDatasetBase, zfs.objects.FilesystemBase, DatasetBase, zfsBase):
#    pass
