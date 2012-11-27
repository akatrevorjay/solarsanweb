
from solarsan.utils import LoggedException
#import logging
import sh
#from collections import defaultdict
import storage.base


class DatasetProperty(storage.base.BaseProperty):
    pass


class DatasetProperties(object):
    """Storage Dataset Properties object
    """

    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, k):
        """Gets dataset property.

        dataset = Dataset('dpool/carp')
        dataset.properties['alloc']

        """
        try:
            return self._get(k)
        except sh.ErrorReturnCode_1:
            raise KeyError

    def __setitem__(self, k, v):
        """Sets dataset property.

        dataset = Dataset('dpool/carp')
        dataset.properties['readonly'] = 'on'

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
        """Gets dataset property.

        dataset = Dataset('dpool/carp')
        dataset.properties._get('alloc', 'free')
        dataset.properties._get('all')

        """
        assert props

        ret = []
        skip = 1
        for line in sh.zfs('get', ','.join(props), self._parent.name):
            if skip > 0:
                skip -= 1
                continue
            line = line.rstrip("\n")
            (obj_name, name, value, source) = line.split(None, 3)
            ret.append(DatasetProperty(self, name, value, source))

        # If we only requested a single property from a single object that
        # isn't the magic word 'all', just return the value.
        if len(props) == 1 and len(ret) == len(props) and 'all' not in props:
            ret = ret[0]
        return ret

    def _set(self, k, v, ignore=False):
        """Sets dataset property.

        dataset = Dataset('dpool/carp')
        dataset.properties._set('readonly', 'on')

        """
        if ignore:
            return

        prop = None
        if isinstance(v, DatasetProperty):
            prop = v
            v = prop.value

        sh.zfs('set', '%s=%s' % (k, v), self._parent.name)

        if prop:
            prop.value = v

    # TODO Delete item == inherit property
    #def __delitem__(self, k):
    #    """Deletes dataset property.
    #    """
    #    try:
    #        return self._inherit(k)
    #    except sh.ErrorReturnCode_1:
    #        raise KeyError

    #def _inherit(self, k):
    #    """Inherits property from parents
    #    """


class Dataset(storage.base.Base):
    """Base Dataset object
    """

    def __init__(self, *args, **kwargs):
        super(Dataset, self).__init__(*args, **kwargs)
        name = kwargs.get('name')
        if name and getattr(self, 'name', None) is not name:
            self.name = name
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        self.properties = DatasetProperties(self)

    #@property
    #def pool(self):
    #    """ Returns the matching Pool for this Dataset """
    #    return storage.all.Pool(name=self.path(0, 1))
    #    #return self._get_type('pool')(name=self.path(0, 1))

    #@property
    #def parent(self):
    #    """ Returns the parent of this Dataset """
    #    path = self.path()
    #    if len(path) == 1:
    #        return None
    #    return self._get_type('dataset')(name='/'.join(path[:-1]))

    # Good candidates to share code once again:
    #def exists
    #def destroy

    @property
    def basename(self):
        return self.path(None, 1)[0]

    @property
    def pool_name(self):
        name = self.path(0, 1)[0]
        if '@' in name:
            name = name.split('@', 1)[0]
        return name

    @classmethod
    def list(cls, args=None, skip=None, props=None, ret=None, type=None):
        """Lists storage datasets.
        """
        if isinstance(args, basestring):
            args = [args]
        elif not args:
            args = []
        if not props:
            props = ['name']
        if not 'guid' in props:
            props.append('guid')
        if not 'type' in props:
            props.append('type')
        if not type:
            type = cls.__name__.lower()

        ret_type = ret or list
        if ret_type == list:
            ret = []
        elif ret_type == dict:
            ret = {}
        else:
            raise LoggedException("Invalid return object type '%s' specified", ret_type)

        # Generate command and execute, parse output
        cmd = sh.zfs.bake('list', '-o', ','.join(props), '-t', type)
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
            objcls = cls._get_type(cols['type'])
            obj = objcls._get_obj(**cols)
            # TODO Update props as well?

            if ret_type == dict:
                ret[name] = obj
            elif ret_type == list:
                ret.append(obj)

        return ret

    @classmethod
    def _get_obj(cls, **kwargs):
        return cls(kwargs['name'])

    @classmethod
    def _get_type(cls, objtype):
        if objtype == 'filesystem':
            cls = Filesystem
        elif objtype == 'volume':
            cls = Volume
        elif objtype == 'snapshot':
            cls = Snapshot
        return cls


# TODO This is 100% broken
class _SnapshottableDatasetMixin(object):
    #def snapshots(self, **kwargs):
    #    """ Lists snapshots of this dataset """
    #    kwargs['type'] = 'snapshot'
    #    return self.children(**kwargs)

    #def filesystems(self, **kwargs):
    #    kwargs['type'] = 'filesystem'
    #    return self.children(**kwargs)

    #def snapshot(self, name, **kwargs):
    #    """ Create snapshot """
    #    zargs = ['snapshot']
    #    if kwargs.get('recursive', False) is True:
    #        zargs.append('-r')
    #    if not self.name:
    #        raise LoggedException("Snapshot was attempted with an empty name")
    #    #if kwargs.get('name_strftime', True) == True:
    #    #    name = timezone.now().strftime(name)
    #    if not self.exists():
    #        raise Exception("Snapshot was attempted on a non-existent dataset '%s'", self.name)
    #    name = '%s@%s' % (self.name, name)
    #    zargs.append(name)
    #
    #    logging.info('Creating snapshot %s with %s', name, kwargs)
    #    ret = iterpipes.check_call(cmd.zfs(*zargs))
    #    return Snapshot(name)
    pass


class Filesystem(Dataset):
    type = 'filesystem'

    def exists(self):
        """Checks if filesystem exists.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.exists()

        """
        try:
            sh.zfs('list', '-t', 'filesystem', self.name)
        except sh.ErrorReturnCode_1:
            return False
        return True

    def create(self):
        """Creates storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.create()

        """
        try:
            sh.zfs('create', self.name)
        except sh.ErrorReturnCode_1:
            # I'm not sure about this; the problem is if it creates the
            # dataset, but fails to mount it for some reason, we're left with
            # the pieces and a simple 1 retval...
            #if self.exists():
            #    self.destroy()
            raise

        # TODO Force scan of this in bg
        return True

    def destroy(self, confirm=False, recursive=False):
        """Destroys storage filesystem.

        filesystem = Filesystem('dpool/tmp/test0')
        filesystem.destroy()

        """
        if not confirm:
            raise LoggedException('Destroy of storage filesystem requires confirm=True')
        opts = ['destroy']
        if recursive:
            opts.append('-r')
        opts.append(self.name)
        sh.zfs(*opts)
        # TODO Force delete of this in bg (with '-d')
        return True


class Volume(Dataset):
    type = 'volume'

    def exists(self):
        """Checks if volume exists.

        volume = Volume('dpool/tmp/test0')
        volume.exists()

        """
        try:
            sh.zfs('list', '-t', 'volume', self.name)
        except sh.ErrorReturnCode_1:
            return False
        # TODO Force scan of this in bg
        return True

    def create(self, size, sparse=False, block_size=None, mkparent=False):
        """Creates storage volume.

        volume = Volume('dpool/tmp/test0')
        volume.create()

        """
        # TODO Check size to make sure it's decent.

        try:
            # -V volume, -s sparse, -b blocksize, -o prop=val
            # -p works like mkdir -p, creates non-existing parent datasets.
            opts = ['create']
            if sparse:
                opts.append('-s')
            if block_size:
                opts.extend(['-b', block_size])
            if mkparent:
                opts.append('-p')
            opts.extend(['-V', size, self.name])

            sh.zfs(*opts)
        except sh.ErrorReturnCode_1:
            # I'm not sure about this; the problem is if it creates the
            # dataset, but fails to mount it for some reason, we're left with
            # the pieces and a simple 1 retval...
            #if self.exists():
            #    self.destroy()
            raise
        # TODO Force scan of this in bg
        return True

    def destroy(self, confirm=False, recursive=False):
        """Destroys storage volume.

        volume = Volume('dpool/tmp/test0')
        volume.destroy()

        """
        if not confirm:
            raise LoggedException('Destroy of storage volume requires confirm=True')
        opts = ['destroy']
        if recursive:
            opts.append('-r')
        opts.append(self.name)
        sh.zfs(*opts)
        # TODO Force delete of this in bg
        return True


class Snapshot(Dataset):
    type = 'snapshot'
    #TODO Check on __init__ if name contains '@' or not. It NEEDS to.

    def exists(self):
        """Checks if snapshot exists.

        snapshot = Snapshot('dpool/tmp/test0@whoa-snap-0')
        snapshot.exists()

        """
        try:
            sh.zfs('list', '-t', 'snapshot', self.name)
        except sh.ErrorReturnCode_1:
            return False
        # TODO Force scan of this in bg
        return True

    def create(self, size):
        """Creates storage snapshot.

        snapshot = Snapshot('dpool/tmp/test0@whoa-snap-0')
        snapshot.create()

        """
        # TODO Check size to make sure it's decent.

        try:
            sh.zfs('snapshot', self.name)
        except sh.ErrorReturnCode_1:
            # I'm not sure about this; the problem is if it creates the
            # dataset, but fails to mount it for some reason, we're left with
            # the pieces and a simple 1 retval...
            #if self.exists():
            #    self.destroy()
            raise
        # TODO Force scan of this in bg
        return True

    def destroy(self, confirm=False, recursive=False):
        """Destroys storage snapshot.

        snapshot = Snapshot('dpool/tmp/test0@whoa-snap-0')
        snapshot.destroy()

        """
        if not confirm:
            raise LoggedException('Destroy of storage snapshot requires confirm=True')
        opts = ['destroy']
        if recursive:
            opts.append('-r')
        opts.append(self.name)
        sh.zfs(*opts)
        # TODO Force delete of this in bg
        return True

    @property
    def snapshot_name(self):
        """ Returns the snapshot name """
        return self.basename.rsplit('@', 1)[1]

    @property
    def filesystem_name(self):
        """ Returns the associated filesystem/volume name """
        return self.basename.rsplit('@', 1)[0]

    #@property
    #def filesystem(self):
    #    """ Returns the associated filesystem for this snapshot """
    #    return Filesystem(self.filesystem_name)
