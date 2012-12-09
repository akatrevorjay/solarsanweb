
#import logging
import sh
#from collections import defaultdict, OrderedDict
#import re
from solarsan.utils import LoggedException, FormattedException
from datetime import datetime
from django.utils import timezone

from analytics.cube import CubeAnalytics
from pypercube.expression import EventExpression, MetricExpression, CompoundMetricExpression
from pypercube.expression import Sum, Min, Max, Median, Distinct

from . import base
#from . import device
from .parsers.pool import ZpoolStatusParser


class PoolAnalytics(CubeAnalytics):
    """Storage Pool Analytics object
    """
    def __init__(self, parent):
        self._parent = parent

    def _get_event_expr(self, f, **kwargs):
        #return EventExpression('pool_iostat', f).eq('pool', self._parent.name).gt(f, 0)
        return EventExpression('pool_iostat', f).eq('pool', self._parent.name)

    def _get_metric_expr(self, f, **kwargs):
        e = kwargs.get('event_expr', self._get_event_expr(f, **kwargs))
        return Median(e)
        #return Sum(e)

    def iops(self, **kwargs):
        return self._render('iops_read', 'iops_write', **kwargs)

    def bandwidth(self, **kwargs):
        return self._render('bandwidth_read', 'bandwidth_write', **kwargs)

    def usage(self, **kwargs):
        return self._render('alloc', 'free', **kwargs)


class PoolProperty(base.BaseProperty):
    """Storage Pool Property object
    """
    pass


class PoolProperties(object):
    """Storage Pool Properties object
    """

    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, k):
        """Gets pool property.

        pool = Pool('dpool')
        pool.properties['alloc']

        """
        try:
            return self._get(k)
        except sh.ErrorReturnCode_1:
            raise KeyError

    def __setitem__(self, k, v):
        """Sets pool property.

        pool = Pool('dpool')
        pool.properties['readonly'] = 'on'

        """
        try:
            return self._set(k, v)
        except sh.ErrorReturnCode_1:
            raise ValueError

    def __iter__(self):
        # TODO yield
        return iter(self._get('all'))

    def dumps(self):
        ret = {}
        for p in self:
            ret[p.name] = p.value
        return ret

    def _get(self, *props):
        """Gets pool property.

        pool = Pool('dpool')
        pool.properties._get('alloc', 'free')
        pool.properties._get('all')

        """
        assert props

        ret = []
        skip = 1
        for line in sh.zpool('get', ','.join(props), self._parent.name):
            if skip > 0:
                skip -= 1
                continue
            line = line.rstrip("\n")
            (obj_name, name, value, source) = line.split(None, 3)
            ret.append(PoolProperty(self, name, value, source))

        # If we only requested a single property from a single object that
        # isn't the magic word 'all', just return the value.
        if len(props) == 1 and len(ret) == len(props) and 'all' not in props:
            ret = ret[0]
        return ret

    def _set(self, k, v, ignore=False):
        """Sets pool property.

        pool = Pool('dpool')
        pool.properties._set('readonly', 'on')

        """
        if ignore:
            return

        prop = None
        if isinstance(v, PoolProperty):
            prop = v
            v = prop.value

        sh.zpool('set', '%s=%s' % (k, v), self._parent.name)

        if prop:
            prop.value = v

    # TODO Delete item == inherit property
    #def __delitem__(self, k):
    #    """Deletes pool property.
    #    """
    #    try:
    #        return self._inherit(k)
    #    except sh.ErrorReturnCode_1:
    #        raise KeyError

    #def _inherit(self, k):
    #    """Inherits property from parents
    #    """


# TODO Enumerate devices on pool from status
class Pool(base.Base):
    """Storage Pool object
    """
    type = 'pool'

    def __init__(self, *args, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)
        name = kwargs.get('name')
        if name and getattr(self, 'name', None) is not name:
            self.name = name
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        self.properties = PoolProperties(self)
        self.analytics = PoolAnalytics(self)

    """
    General
    """

    def exists(self):
        """Checks if pool exists.

        pool = Pool('dpool')
        pool.exists()

        """
        try:
            sh.zpool('list', self.name)
        except sh.ErrorReturnCode_1:
            return False
        return True

    def is_healthy(self):
        return unicode(self.properties['health']) == u'ONLINE'

    def is_degraded(self):
        return unicode(self.properties['health']) == u'DEGRADED'

    #@property
    def health_state_str(self):
        if self.is_healthy:
            return 'success'
        elif self.is_degraded:
            return 'warning'
        else:
            return 'error'

    def create(self, *devices):
        """Creates storage pool.

        pool = Pool('dpool')
        pool.create(Mirror(Disk('sda'), Disk('sdb')),
            Disk('sda') + Disk('sdb'),
            Log('sda') + Log('sdb'),
            Cache('sde'),
            Cache('sdf'),
            )

        """
        cmd = sh.zpool.bake('create', self.name)

        args = []
        for dev in devices:
            if getattr(dev, '_zpool_args'):
                args.extend(dev._zpool_args())
            else:
                args.append(dev._zpool_arg())

        # TODO Retval check, pool check, force a Zfs import scan in bg
        #try:
        cmd(*args)
        #except rv.ErrorReturnCode_1:
        #    return False
        return True

    def destroy(self, confirm=False):
        """Destroys storage pool.

        pool = Pool('dpool')
        pool.destroy()

        """
        if not confirm:
            raise LoggedException('Destroy of storage pool requires confirm=True')
        sh.zpool('destroy', self.name)
        return True

    def status(self):
        """Returns status of storage pool.

        pool = Pool('dpool')
        pool.status()

        """
        p = ZpoolStatusParser()
        out = sh.zpool('status', self.name).stdout
        ret = p(out)
        return ret[self.name]

    def iostat(self, capture_length=30):
        """Returns iostat of storage pool.

        pool = Pool('dpool')
        pool.iostat()

        """
        timestamp = None
        skip_past_dashline = False
        for line in sh.zpool('iostat', '-T', 'u', self.name, capture_length, 2):
            line = line.rstrip("\n")

            # Got a timestamp
            if line.isdigit():
                # If this is our first record, skip till we get the header seperator
                if not timestamp:
                    skip_past_dashline = True
                # TZify the timestamp
                timestamp = timezone.make_aware(
                    datetime.fromtimestamp(int(line)),
                    timezone.get_current_timezone())
                continue

            # If we haven't gotten the dashline yet, wait till the line after it
            if skip_past_dashline:
                if line.startswith('-----'):
                    skip_past_dashline = False
                continue
            # Either way, let's not worry about them
            if line.startswith('-----'):
                continue

            # If somehow we got here without a timestamp, something is probably wrong.
            if not timestamp:
                raise LoggedException("Got unexpected input from zpool iostat: %s", line)

            # Parse iostats output
            j = {}
            (j['name'],
             j['alloc'], j['free'],
             j['iops_read'], j['iops_write'],
             j['bandwidth_read'], j['bandwidth_write']) = line.strip().split()
            j['timestamp'] = timestamp
            j.pop('name')
            return j

    @classmethod
    def list(cls, args=None, skip=None, props=None, ret=None):
        """Lists storage pools.
        """
        if isinstance(args, basestring):
            args = [args]
        elif not args:
            args = []
        if not props:
            props = ['name']
        if not 'guid' in props:
            props.append('guid')

        ret_type = ret or list
        if ret_type == list:
            ret = []
        elif ret_type == dict:
            ret = {}
        else:
            raise LoggedException("Invalid return object type '%s' specified", ret_type)

        # Generate command and execute, parse output
        cmd = sh.zpool.bake('list', '-o', ','.join(props))
        header = None
        for line in cmd(*args):
            line = line.rstrip("\n")
            if not header:
                header = line.lower().split()
                continue
            cols = dict(zip(header, line.split()))
            name = cols['name']

            if skip and skip == name:
                continue

            ## FIXME This hsould be handled in __init__ of document subclass me thinks
            obj = cls._get_obj(**cols)
            # TODO Update props as well?

            if ret_type == dict:
                ret[name] = obj
            elif ret_type == list:
                ret.append(obj)

        return ret

    @classmethod
    def _get_obj(cls, **kwargs):
        return cls(kwargs['name'])

    """
    Device
    """

    def add(self, device):
        """Grow pool by adding new device.

        pool = Pool('dpool')
        pool.add(
            Disk('sda') + Disk('sdb'),
            )

        """
        cmd = sh.zpool.bake('add', self.name)

        args = []
        for dev in [device]:
            if getattr(dev, '_zpool_args'):
                args.extend(dev._zpool_args())
            else:
                args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def remove(self, device):
        """Removes device from pool.

        pool = Pool('dpool')
        pool.remove(Disk('sdc'))

        """
        cmd = sh.zpool.bake('remove', self.name)

        args = []
        for dev in [device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def attach(self, device, new_device):
        """Attaches new device to existing device, creating a device mirror.

        pool = Pool('dpool')
        pool.attach(Disk('sdb'), Disk('sdc'))

        """
        cmd = sh.zpool.bake('attach', self.name)

        args = []
        for dev in [device, new_device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def detach(self, device):
        """Detaches existing device from an existing device mirror.

        pool = Pool('dpool')
        pool.detach('sdb')

        """
        cmd = sh.zpool.bake('detach', self.name)

        args = []
        for dev in [device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True

    def replace(self, device, new_device):
        """Replacees device with new device.

        pool = Pool('dpool')
        pool.replace(Disk('sdb'), Disk('sdc'))

        """
        cmd = sh.zpool.bake('replace', self.name)

        args = []
        for dev in [device, new_device]:
            args.append(dev._zpool_arg())

        cmd(*args)
        return True
