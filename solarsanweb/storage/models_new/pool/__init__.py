
import mongoengine as m

#import zfs
import zfs.cmd
import zfs.objects

#import storage.models.base
#import storage.models.filesystem
#import storage.models.volume
#import storage.models.snapshot

from .. import zfsBaseDocument, zfsBase

#from ..filesystem import Filesystem
#from ..volume import Volume
#from ..snapshot import Snapshot

from .vdev import VDevChildDocument, VDevMirror, VDevDisk
VDEV_TYPE_MAP = {'root': None,
                 'mirror': VDevMirror,
                 'disk': VDevDisk, }


from analytics.cube import CubeAnalytics
from pypercube.expression import EventExpression, Median  # MetricExpression, CompoundMetricExpression
#from pypercube.expression import Sum, Min, Max, Median, Distinct


class PoolAnalytics(CubeAnalytics):
    def __init__(self, pool):
        self.pool = pool

    def _get_event_expr(self, f, **kwargs):
        return EventExpression('pool_iostat', f).eq('pool', self.pool.name).gt(f, 0)

    def _get_metric_expr(self, f, **kwargs):
        e = kwargs.get('event_expr', self._get_event_expr(f, **kwargs))
        return Median(e)

    def iops(self, **kwargs):
        return self._render('iops_read', 'iops_write', **kwargs)

    def bandwidth(self, **kwargs):
        return self._render('bandwidth_read', 'bandwidth_write', **kwargs)

    def usage(self, **kwargs):
        return self._render('alloc', 'free', **kwargs)


class PoolDocument(zfsBaseDocument):
    meta = {'collection': 'pools',
            'abstract': True, }
    version = m.IntField()
    state = m.IntField()
    txg = m.IntField()
    #guid = m.StringField(unique=True, required=True, primary_key=True)
    guid = m.StringField(unique=True)
    hostname = m.StringField()
    vdevs = m.ListField(m.EmbeddedDocumentField(VDevChildDocument))

    VDEV_TYPE_MAP = VDEV_TYPE_MAP

    analytics = None

    def __init__(self, *args, **kwargs):
        self.analytics = PoolAnalytics(self)
        return super(PoolDocument, self).__init__(*args, **kwargs)

    def reload_zdb(self):
        """ Snags pool status and vdev info from zdb as zpool status kind of sucks """
        z = zfs.cmd.ZdbCommand('-C', '-v')
        ret = z(ofilter=zfs.cmd.SafeYamlFilter)
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
        obj_cls = self.VDEV_TYPE_MAP[obj_type]
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


class Pool(PoolDocument, zfs.objects.PoolBase, zfsBase):
    pass
