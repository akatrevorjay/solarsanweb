
#from django.db import models
#from jsonfield import JSONField
import os
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
#import sh

import mongoengine as m
from datetime import datetime
#from django.utils import timezone
from django.core.urlresolvers import reverse
from django.utils.text import capfirst

import rtslib
import storage.pool
import storage.dataset
import storage.device
from solarsan.utils import FormattedException, LoggedException
from solarsan.utils import convert_bytes_to_human

from .parsers.pool import ZdbPoolCacheParser

import cluster.models as cm


"""
Base
"""

#class EnablementQuerySet(m.QuerySet):
#    def enabled(self, queryset):
#        pass
#    def disabled(self, queryset):
#        pass


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
        elif type == 'disk':
            return 'DSK'
        #elif type == 'mirror':
        #    return 'MIR'
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


class VDevBaseDocument(BaseMixIn, m.Document):
    meta = {'abstract': True,
            'allow_inheritance': True,
            #'ordering': ['-created'],
            }

    #VDEV_TYPES=['root', 'mirror', 'disk']
    #type = m.StringField(required=True, choices=VDEV_TYPES)
    #vdev_id = m.IntField(unique=True, primary_key=True)
    vdev_id = m.IntField()
    guid = m.StringField(unique=True)

    created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    modified = m.DateTimeField(default=datetime.now())

    def __repr__(self):
        cls_name = self.__class__.__name__
        data = {}
        path = getattr(self, 'path', None)
        if path:
            data['path'] = path
        guid = getattr(self, 'guid', None)
        if guid:
            data['guid'] = guid
        if hasattr(self, 'is_parent') and self.is_parent:
            data['children'] = self.children
        return "<%s: %s>" % (cls_name, data)

    def pretty(self):
        cls_name = self.__class__.__name__
        data = {}
        path = getattr(self, 'path', None)
        if path:
            data['path'] = path
        guid = getattr(self, 'guid', None)
        if guid:
            data['guid'] = guid
        if hasattr(self, 'is_parent') and self.is_parent:
            data['children'] = self.children
        return "%s" % (cls_name, data)

    def pretty_dict(self):
        def do_vdev(vdev):
            ret = {'type': vdev.type,
                   #'_obj': vdev,
                   #'modified': vdev.modified,
                   #'created': vdev.created,
                   #'id': vdev.vdev_id,
                   'guid': vdev.guid,
                   }
            if vdev.is_parent:
                ret['children'] = [do_vdev(child) for child in vdev.children]
            else:
                ret['path'] = vdev.path
                ret['whole_disk'] = bool(vdev.whole_disk)
                ret['is_healthy'] = vdev.is_healthy
                #ret['state'] = vdev.state
                ret['health'] = vdev.health
            return ret
        return do_vdev(self)


#class VDevRoot(VDevBaseDocument):
#    #pool_guid = m.StringField()
#    #vdev_id = m.IntField()
#    state = m.IntField()
#    txg = m.IntField()


#class VDevPool(VDevBaseDocument):
#    version = m.IntField()
#    name = m.StringField()
#    state = m.IntField()
#    txg = m.IntField()
#    hostname = m.StringField()
#
#    vdev_children = m.IntField()
#    vdev_tree = m.MapField(m.ReferenceField(VDevRoot, dbref=False, reverse_delete_rule=m.CASCADE))
#
#    #def children(self):
#    #    pass


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
    type = 'disk'
    state = m.StringField()

    @property
    def children(self):
        return [self]

    @property
    def is_parent(self):
        return False

    @property
    def path_pretty(self):
        return self.path.replace('/dev/', '')

    @property
    def asize_pretty(self):
        return convert_bytes_to_human(self.asize)

    @property
    def health(self):
        #if self.is_healthy:
        #    return 'Good'
        #else:
        if True:
            state = self.state or 'UNKNOWN'
            return capfirst(state.lower())

    @property
    def is_healthy(self):
        return self.state == 'ONLINE'

    def to_device(self):
        return storage.device.Device(self.path)


class VDevMirror(VDevChildDocument):
    children = m.ListField(m.ReferenceField(VDevDisk, dbref=False, reverse_delete_rule=m.CASCADE))
    type = 'mirror'

    @property
    def is_parent(self):
        return True

    @property
    def asize_pretty(self):
        return max([x.asize_pretty for x in self.children])

    #@property
    #def id(self):
    #    return self.vdev_id


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

    #state = m.IntField()
    state = m.StringField()
    #errors = m.StringField()
    #action = m.StringField()
    #status = m.StringField()
    #config = m.StringField()

    txg = m.IntField()
    #guid = m.StringField(unique=True, required=True, primary_key=True)
    #guid = m.StringField(unique=True)
    guid = m.StringField(unique=True, required=False)
    hostname = m.StringField()
    #vdevs = m.ListField(m.EmbeddedDocumentField(VDevChildDocument))
    vdevs = m.ListField(m.ReferenceField(VDevChildDocument, dbref=False, reverse_delete_rule=m.CASCADE))

    _VDEV_TYPE_MAP = _VDEV_TYPE_MAP

    @m.queryset_manager
    def objects_clustered(doc_cls, queryset):
        return queryset.filter(is_clustered=True)

    @m.queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(enabled__ne=False)

    @m.queryset_manager
    def objects_including_disabled(doc_cls, queryset):
        return queryset

    """
    Clustering
    """

    is_clustered = m.BooleanField(default=False)
    #cluster_is_active = m.BooleanField()
    cluster_peer = m.ReferenceField(cm.Peer, dbref=False)
    cluster_state = m.DictField()

    def cluster_promote(self, force=False):
        """
        1. Tell peer PENDING_PROMOTION
        2. Wait for peer to respond OK and peer state to change to PENDING_DEMOTION
          a. If timeout occurs or FAILED_DEMOTION is received:
              If force==True: Forcefully takeover
              Otherwise: Spew errors like it's y2k
          b. Otherwise: Wait for DEMOTED and constant heartbeat replies
        3. Stop local cluster target
        4. Connect to peer's cluster target
        5. Import pool
        """
        pass

    def cluster_demote(self, force=False):
        """
        1. Tell peer PENDING_DEMOTION
        2. Wait for peer to respond OK, PENDING_PROMOTION
          a. If timeout occurs:
            1. Spew errors like it's y2k
            2. Set state to FAILED_DEMOTION
        3. Stop any targets on pool
        4. Export pool
        5. Share out local pool disks through my cluster target
        5. Disconnect from cluster targets for this pool
        6. Tell peer DEMOTED
        """
        pass

    def cluster_heartbeat(self):
        return self.cluster_peer.heartbeat()

    """
    Now back to your normal daily programming
    """

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
            obj.reload_zfs()
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
        #return Filesystem.objects.filter(pool=self)
        return self.filesystem.filesystems()

    def volumes(self):
        #return Volume.objects.filter(pool=self)
        return self.filesystem.volumes()

    def children(self):
        return list(self.filesystems()) + list(self.volumes())

    """
    Zfs Metadata Importing / Zpool/Zdb Parsing
    """

    def reload_zfs(self):
        self._reload_zdb()
        self._reload_status()
        #if self._changed_fields:
        #    self.save()

    # TODO filter_by_attrs here
    #def get_vdev_by_guid(self, guid, vdevs=None):
    #    if not vdevs:
    #        vdevs = self.vdevs
    #    for vdev in vdevs:
    #        if vdev.is_parent:
    #
    #        if vdev.guid == guid:
    #            return vdev

    #def get_vdev_by_path(self, path):
    #    for vdev in self.vdevs:
    #        if vdev.is_parent:
    #
    #        if vdev.path == path:
    #            return vdev

    def guess_vdev_by_basename(self, basename, vdevs=None):
        if not vdevs:
            vdevs = self.vdevs
        for vdev in vdevs:
            if vdev.is_parent:
                vdev = self.guess_vdev_by_basename(basename, vdevs=vdev.children)
                if vdev:
                    return vdev
            else:
                if os.path.basename(vdev.path) == basename:
                    return vdev
                # TODO Fix bug in udev device discovery where it doesn't look
                # for zfs part labels on iscsi devices
                if os.path.basename(vdev.path) == '%s-part1' % basename:
                    return vdev

    def _reload_status(self):
        """ Snags pool status and vdev info from zpool """
        # TODO Add to vdev info error counts and such
        s = self.status()

        #for k in ['status', 'errors', 'scan', 'see', 'state', 'action', 'config']:
        #for k in ['errors', 'scan', 'see', 'state', 'action', 'config']:
        #    setattr(self, k, s[k])
        #self.pool_status = s['status']

        for k, v in s['config'].items():
            if k == self.name:
                self.state = v['state']
            else:
                vdev = self.guess_vdev_by_basename(k)
                #logging.info("k=%s v=%s vdev=%s", k, v, vdev)
                if vdev:
                    #logging.info("Got vdev=%s", vdev)
                    vdev.state = v['state']

    def _reload_zdb(self):
        """ Parses pool status and vdev info from given zdb data """
        p = ZdbPoolCacheParser()
        ret = p()
        ret = ret[self.name]

        # Basic info
        # hostname, vdev_children, vdev_tree, name(single quoted)
        self.guid = unicode(ret['pool_guid'])
        #self.state = ret['state']
        self.txg = ret['txg']
        self.version = ret['version']
        # Just a count
        #vdev_children = ret['vdev_children']
        # VDev parser
        self._reload_zdb_vdev_tree(ret['vdev_tree'])

    def _reload_zdb_vdev_tree(self, cur):
        def parse_vdev(cls, data):
            obj, created = cls.objects.get_or_create(
                guid=unicode(data.pop('guid')), )
            data['vdev_id'] = data.pop('id', None)
            for v in cls._fields.keys():
                if v == 'id':
                    continue
                if v in data:
                    setattr(obj, v, unicode(data[v]))
            return obj

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
                    cobj = self._reload_zdb_vdev_tree(cur=v)
                    children.append(cobj)
                    #children.insert(cobj.id, cobj)

        if obj:
            if children:
                obj.children = children
            if obj._changed_fields:
                obj.save()
            return obj
        elif obj_type == 'root':
            self.vdevs = children
        else:
            raise Exception("Could not parse VDev tree")

    """
    Devices
    """

    @property
    def devices(self):
        ret = {}

        def do_vdev(vdev):
            ret = {'type': vdev.type, '_obj': vdev}
            if vdev.is_parent:
                ret['children'] = [do_vdev(child) for child in vdev.children]
            else:
                ret['path'] = vdev.path
            return ret

        for vdev in self.vdevs:
            ret[vdev.guid] = do_vdev(vdev)

        return ret

    def pretty_devices(self):
        return [vdev.pretty_dict() for vdev in self.vdevs]


"""
Dataset
"""


class _DatasetBase(_StorageBaseDocument):
    meta = {'collection': 'datasets',
            'allow_inheritance': True, }
            #'abstract': True, }
    pool = m.ReferenceField(Pool,
                            reverse_delete_rule=m.CASCADE,
                            dbref=False)

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

    @m.queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(enabled__ne=False)

    @m.queryset_manager
    def objects_including_disabled(doc_cls, queryset):
        return queryset



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

    @m.queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(enabled__ne=False)

    @m.queryset_manager
    def objects_including_disabled(doc_cls, queryset):
        return queryset


class Snapshot(_DatasetBase, storage.dataset.Snapshot):
    """Storage Snapshot object
    """
    def __init__(self, *args, **kwargs):
        super(Snapshot, self).__init__(*args, **kwargs)
        if getattr(self, '_init'):
            self._init(*args, **kwargs)

    @m.queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(enabled__ne=False)

    @m.queryset_manager
    def objects_including_disabled(doc_cls, queryset):
        return queryset



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

    @property
    def backstore(self):
        """ Returns backstore object """
        if not self.backstore_wwn:
            #raise self.DoesNotExist("Could not get backstore for Volume '%s' as it has no backstore_wwn attribute", self.name)
            self._create_backstore()

        root = rtslib.RTSRoot()
        for so in root.storage_objects:
            if so.wwn == self.backstore_wwn:
                return so

        logging.error("Could not get block backstore for Volume '%s' specified as wwn=%s as it does not exist.. " +
                      "Trying to create new one instead.", self.name, self.backstore_wwn or None)
        orig_wwn = self.backstore_wwn
        try:
            #return self._create_backstore(wwn=orig_wwn)
            return self._create_backstore()
        except rtslib.RTSLibError:
            try:
                self.backstore_wwn = orig_wwn
                if self.pk:
                    self.save()
            finally:
                logging.error("Could not create a new block backstore for Volume '%s', giving up..", self.name)
                return None

        #logging.error("Created a new block backstore for Volume '%s' specified as wwn=%s.", self.name, self.backstore_wwn or None)
        #return None

    def _create_backstore(self, **kwargs):
        """ Creates a backing storage object for target usage """
        if not 'wwn' in kwargs or kwargs.get('wwn') != self.backstore_wwn:
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

    def _delete_backstore(self):
        """ Delete a backing storage object """
        backstore = self.backstore
        logging.info("Deleting block backstore for volume '%s' specified as wwn=%s", self, backstore.wwn)
        backstore.delete()
        self.backstore_wwn = None
        if self.pk:
            self.save()
        return True

    @m.queryset_manager
    def objects(doc_cls, queryset):
        return queryset.filter(enabled__ne=False)

    @m.queryset_manager
    def objects_including_disabled(doc_cls, queryset):
        return queryset
