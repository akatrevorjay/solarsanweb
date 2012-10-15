
#from dj import reverse

from datetime import datetime
import mongoengine as m

#import zfs

from .. import BaseMixIn
#from . import ZFS_TYPE_MAP
#from .property import Property


"""
VDevs
"""


class VDevBaseDocument(BaseMixIn, m.EmbeddedDocument):
    meta = {'abstract': True, }
            #'ordering': ['-created']}

    #VDEV_TYPES=['root', 'mirror', 'disk']
    #type = m.StringField(required=True, choices=VDEV_TYPES)
    #vdev_id = m.IntField(unique=True, primary_key=True)
    vdev_id = m.IntField()
    guid = m.StringField(unique=True)

    created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())


class VDevRootDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    #pool_guid = m.StringField()
    #vdev_id = m.IntField()
    state = m.IntField()
    txg = m.IntField()


class VDevRoot(VDevRootDocument):
    pass


class VDevPoolDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    version = m.IntField()
    name = m.StringField()
    state = m.IntField()
    txg = m.IntField()
    hostname = m.StringField()

    vdev_children = m.IntField()
    vdev_tree = m.MapField(m.EmbeddedDocumentField(VDevRoot))


class VDevPool(VDevPoolDocument):
    #def children(self):
    #    pass
    pass


class VDevChildDocument(VDevBaseDocument):
    meta = {'abstract': True, }
    ashift = m.IntField()
    asize = m.IntField()
    create_txg = m.IntField()
    # Only on mirrored vdevs
    DTL = m.IntField()
    resilvering = m.IntField()
    is_log = m.IntField()
    metaslab_array = m.IntField()
    metaslab_shift = m.IntField()


from solarsan.utils import convert_bytes_to_human


class VDevDiskDocument(VDevChildDocument):
    meta = {'abstract': True, }
    path = m.StringField()
    whole_disk = m.IntField()

    @property
    def path_pretty(self):
        return self.path.replace('/dev/', '')

    @property
    def asize_pretty(self):
        return convert_bytes_to_human(self.asize)

    @property
    def health(self):
        # TODO disk health
        return 'Good'

    @property
    def type(self):
        return 'disk'


class VDevDisk(VDevDiskDocument):
    pass


class VDevMirrorDocument(VDevChildDocument):
    meta = {'abstract': True, }
    children = m.ListField(m.EmbeddedDocumentField(VDevDisk))


class VDevMirror(VDevMirrorDocument):
    pass
