
#import mongoengine as m
import rtslib

#import zfs
#import zfs.cmd
import zfs.objects

#from .pool import Pool
#from .filesystem import Filesystem
#from .volume import Volume

from .base import zfsBase
from .dataset import DatasetDocument, DatasetBase, SnapshottableDatasetBase

from solarsan.utils import FormattedException  # LoggedException


class VolumeDocument(DatasetDocument):
    #meta = {'abstract': True,}
    backstore_wwn = m.StringField()

    @property
    def device_path(self):
        return '/dev/zvol/%s' % self.name

    class DoesNotExist(FormattedException):
        pass

    def backstore(self):
        """ Returns backstore object """
        if not self.backstore_wwn:
            raise self.DoesNotExist("Could not get backstore for Volume '%s' as it has no backstore_wwn attribute", self.name)
        root = rtslib.RTSRoot()
        for so in root.storage_objects:
            if so.wwn == self.backstore_wwn:
                return so
        #raise LoggedException("Could not get block backstore for Volume '%s' specified as wwn=%s as it does not exist", self.name, self.backstore_wwn or None)
        return None

    def create_backstore(self, **kwargs):
        """ Creates a backing storage object for target usage """
        assert not self.backstore_wwn
        if not 'name' in kwargs:
            kwargs['name'] = self.name.replace('/', '_')
        name = kwargs.pop('name')
        kwargs['dev'] = self.device_path

        logging.info("Creating backstore for volume '%s' with name '%s' (params=%s)", self, name, kwargs)
        backstore = rtslib.BlockStorageObject(name, **kwargs)
        self.backstore_wwn = backstore.wwn
        if self.pk:
            self.save()
        return backstore

    def delete_backstore(self):
        """ Delete a backing storage object """
        backstore = self.backstore()
        logging.info("Deleting block backstore for volume '%s' specified as wwn=%s", self, backstore.wwn)
        backstore.delete()
        self.backstore_wwn = None
        if self.pk:
            self.save()
        return True


class Volume(VolumeDocument, SnapshottableDatasetBase, zfs.objects.VolumeBase, DatasetBase, zfsBase):
    pass
