
#from django.db import models
#from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import sh
import yaml

import mongoengine as m
from datetime import datetime
#from django.utils import timezone
from django.core.urlresolvers import reverse

import rtslib
import storage.pool
import storage.dataset
from solarsan.utils import FormattedException  # LoggedException
from solarsan.utils import convert_bytes_to_human


"""
Base
"""


class ReprMixIn(object):
    def __repr__(self):
        for k in ['name', 'guid', 'id']:
            name = getattr(self, k, None)
            if name:
                break
        return "<%s: %s>" % (self.__class__.__name__, name)

    def __unicode__(self):
        name = getattr(self, 'name', self.__repr__())
        return name


class BaseMixIn(ReprMixIn):
    @property
    def short_type(self):
        if type == 'filesystem':
            return 'FS'
        elif type == 'pool':
            return 'POOL'
        elif type == 'volume':
            return 'VOL'
        else:
            return 'TGT'


"""
Base
"""


class _StorageBaseDocument(BaseMixIn, m.Document):
    meta = {'abstract': True,
            'ordering': ['-created']}
    name = m.StringField(required=True, unique=True)
    #type = m.StringField(required=True)
    #name = m.StringField()
    # TODO Need to make this store as a dict in parent too
    #props = m.MapField(m.EmbeddedDocumentField(Property))
    #misc = m.DictField()
    importing = m.BooleanField()

    created = m.DateTimeField(default=datetime.now())
    # TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())
    enabled = m.BooleanField()

    def __init__(self, *args, **kwargs):
        # Apparently m.Document accepts no init *args
        # for cls in self.
        #BaseMixIn.__init__()
        super(_StorageBaseDocument, self).__init__(**kwargs)

    #def get_absolute_url(self, *args):
    #    """ Gets URL for object """
    #    ret = '/storage/%ss' % self.type
    #    if args:
    #        ret += '/' + '/'.join(args)
    #    ret += '/%s' % self.name
    #    return ret

    def get_absolute_url(self, *args):
        """ Gets URL for object """
        name = getattr(self, 'name', None)
        type = getattr(self, 'type', None)
        assert name
        assert type
        return reverse(type, None, None, {'slug': name, }, )

    def dumps(self):
        return self.__dict__


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


class VDevRoot(VDevBaseDocument):
    #pool_guid = m.StringField()
    #vdev_id = m.IntField()
    state = m.IntField()
    txg = m.IntField()


class VDevPool(VDevBaseDocument):
    version = m.IntField()
    name = m.StringField()
    state = m.IntField()
    txg = m.IntField()
    hostname = m.StringField()

    vdev_children = m.IntField()
    vdev_tree = m.MapField(m.EmbeddedDocumentField(VDevRoot))

    #def children(self):
    #    pass


class VDevChildDocument(VDevBaseDocument):
    ashift = m.IntField()
    asize = m.IntField()
    create_txg = m.IntField()
    # Only on mirrored vdevs
    DTL = m.IntField()
    resilvering = m.IntField()
    is_log = m.IntField()
    metaslab_array = m.IntField()
    metaslab_shift = m.IntField()


class VDevDisk(VDevChildDocument):
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

    type = 'disk'


class VDevMirror(VDevChildDocument):
    children = m.ListField(m.EmbeddedDocumentField(VDevDisk))

    type = 'mirror'


_VDEV_TYPE_MAP = {'root': None,
                  'mirror': VDevMirror,
                  'disk': VDevDisk, }


"""
Pool
"""


class Pool(_StorageBaseDocument, storage.pool.Pool):
    """Storage Pool Mongo Document
    """
    meta = {'collection': 'pools'}
    version = m.IntField()
    state = m.IntField()
    txg = m.IntField()
    #guid = m.StringField(unique=True, required=True, primary_key=True)
    #guid = m.StringField(unique=True)
    guid = m.StringField(unique=True, required=False)
    hostname = m.StringField()
    vdevs = m.ListField(m.EmbeddedDocumentField(VDevChildDocument))

    _VDEV_TYPE_MAP = _VDEV_TYPE_MAP

    def __init__(self, *args, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)
        if getattr(self, '_init'):
            self._init(*args, **kwargs)

    @classmethod
    def _get_obj(cls, **kwargs):
        obj, created = cls.objects.get_or_create(name=kwargs['name'],
                                                 auto_save=False)
        if created:
            logging.warning("Found unknown '%s'", obj)
            obj.reload_zdb()
            obj.save()
        return obj

    """
    Children
    """

    @property
    def filesystem(self):
        """Returns the matching Filesystem for this Pool
        """
        return Filesystem._get_obj(name=self.name)

    def filesystems(self):
        return Filesystem.objects.filter(pool=self)

    def volumes(self):
        return Volume.objects.filter(pool=self)

    def children(self):
        return list(self.filesystems()) + list(self.volumes())

    """
    Zdb Parsing
    """

    def reload_zdb(self):
        """ Snags pool status and vdev info from zdb as zpool status kind of sucks """
        zdb = sh.zdb('-C', '-v')
        ret = yaml.safe_load(zdb.stdout)
        ret = ret[self.name]
        self._parse_zdb(ret)

    def _parse_zdb(self, ret):
        """ Parses pool status and vdev info from given zdb data """
        # Basic info
        # hostname, vdev_children, vdev_tree, name(single quoted)
        self.guid = unicode(ret['pool_guid'])
        self.state = ret['state']
        self.txg = ret['txg']
        self.version = ret['version']
        # Just a count
        #vdev_children = ret['vdev_children']
        # VDev parser
        self._parse_zdb_vdev_tree(ret['vdev_tree'])

    def _parse_zdb_vdev_tree(self, cur):
        def parse_vdev(cls, data):
            obj = {}
            data['vdev_id'] = data.pop('id', None)
            for v in cls._fields.keys():
                if v == 'id':
                    continue
                if v in data:
                    obj[v] = unicode(data[v])
            return cls(**obj)

        obj_type = cur['type']
        obj_cls = self._VDEV_TYPE_MAP[obj_type]
        if obj_cls:
            obj = parse_vdev(obj_cls, cur)
        else:
            obj = None
        children = []

        # Don't look for children with a type of disk, cause disks don't let disks have disks
        if obj_type in ['mirror', 'root']:
            # Walk through recursively
            for v in cur.itervalues():
                if isinstance(v, dict):
                    cobj = self._parse_zdb_vdev_tree(cur=v)
                    children.append(cobj)
                    #children.insert(cobj.id, cobj)

        if obj:
            obj.children = children
            return obj
        elif obj_type == 'root':
            self.vdevs = children
        else:
            raise Exception("Could not parse VDev tree")


"""
Dataset
"""


class _DatasetBase(_StorageBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True, }
            #'abstract': True, }
    pool = m.ReferenceField(Pool,
                            reverse_delete_rule=m.CASCADE)

    #parent = m.ReferenceField(_DatasetBase,
    #                          reverse_delete_rule=m.CASCADE)
    parent = m.GenericReferenceField()

    #guid = m.StringField(unique=True)
    guid = m.StringField()

    @classmethod
    def _get_obj(cls, **kwargs):
        obj, created = cls.objects.get_or_create(name=kwargs['name'],
                                                 #pool=self,
                                                 auto_save=False)
        if created:
            logging.error("Found unknown '%s'", obj)
            obj.pool = Pool.objects.get(name=obj.pool_name)

            if 'guid' in kwargs:
                obj.guid = kwargs['guid']
            else:
                try:
                    obj.guid = unicode(obj.properties['guid'])
                except KeyError:
                    pass

            obj.save()
        else:
            if obj.importing:
                logging.info("Found known '%s'", obj)
                obj.update(unset__importing=True)
                obj.save()
        return obj

    @classmethod
    def _get_type(cls, objtype):
        if objtype == 'filesystem':
            cls = Filesystem
        elif objtype == 'volume':
            cls = Volume
        elif objtype == 'snapshot':
            cls = Snapshot
        return cls


class Dataset(_DatasetBase, storage.dataset.Dataset):
    pass


class _SnapshottableDatasetMixin(object):
    def snapshots(self):
        return Snapshot.objects.filter(name__startswith='%s@' % self.name)


class Filesystem(_DatasetBase, _SnapshottableDatasetMixin, storage.dataset.Filesystem):
    """Storage Filesystem object
    """
    def __init__(self, *args, **kwargs):
        super(Filesystem, self).__init__(*args, **kwargs)
        if getattr(self, '_init'):
            self._init(*args, **kwargs)

    def filesystems(self):
        return Filesystem.objects.filter(name__startswith='%s/' % self.name)

    def volumes(self):
        return Volume.objects.filter(name__startswith='%s/' % self.name)

    def children(self):
        return list(self.filesystems()) + list(self.volumes()) + list(self.snapshots())


class Snapshot(_DatasetBase, storage.dataset.Snapshot):
    """Storage Snapshot object
    """
    def __init__(self, *args, **kwargs):
        super(Snapshot, self).__init__(*args, **kwargs)
        if getattr(self, '_init'):
            self._init(*args, **kwargs)


"""
Volumes / Targets
"""


class Volume(_DatasetBase, _SnapshottableDatasetMixin, storage.dataset.Volume):
    """Storage Volume object
    """
    #meta = {'abstract': True,}
    backstore_wwn = m.StringField()

    def __init__(self, *args, **kwargs):
        super(Volume, self).__init__(*args, **kwargs)
        if getattr(self, '_init'):
            self._init(*args, **kwargs)

    @property
    def device_path(self):
        return '/dev/zvol/%s' % self.name

    class DoesNotExist(FormattedException):
        pass

    def snapshots(self):
        return Snapshot.objects.filter(name__startswith='%s@' % self.name)

    def children(self):
        return list(self.snapshots())

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
