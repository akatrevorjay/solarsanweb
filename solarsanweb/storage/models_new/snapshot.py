
#import mongoengine as m

#import zfs
#import zfs.cmd
import zfs.objects

from .base import zfsBase
from .dataset import DatasetDocument, DatasetBase, SnapshottableDatasetBase


"""
Snapshot
"""


class SnapshotDocument(DatasetDocument):
    #meta = {'abstract': True,}
    pass


class Snapshot(SnapshotDocument, zfs.objects.SnapshotBase, DatasetBase, zfsBase):
    pass
