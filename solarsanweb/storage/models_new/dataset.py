
import mongoengine as m

#import zfs
#import zfs.cmd
import zfs.objects


"""
Dataset
"""

from . import zfsBaseDocument, zfsBase
from .pool import Pool

class DatasetDocument(zfsBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True, }
            #'abstract': True, }
    pool = m.ReferenceField(Pool,
                            reverse_delete_rule=m.CASCADE)
    parent = m.GenericReferenceField()
    #parent = m.ReferenceField(DatasetDocument,
    #                          reverse_delete_rule=m.CASCADE)
    guid = m.StringField(unique=True)

    #def __init__(self, *args, **kwargs):
    #    return super(DatasetDocument, self).__init__(*args, **kwargs)

    #def children(self, **kwargs):
    #    return super(DatasetDocument, self).children(**kwargs)


class DatasetBase(zfs.objects.DatasetBase):
    pass


class Dataset(DatasetDocument, DatasetBase, zfsBase):
    pass



class SnapshottableDatasetBase(zfs.objects.SnapshottableDatasetBase):
    def filesystems(self):
        return Filesystem.objects.filter(pool=self.pool, name__startswith='%s/' % self.name)

    def volumes(self):
        return Volume.objects.filter(pool=self.pool, name__startswith='%s/' % self.name)

    def snapshots(self):
        return Snapshot.objects.filter(pool=self.pool, name__startswith='%s/' % self.name)
