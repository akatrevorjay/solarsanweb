from copy import copy


def filter_by_attrs(args, **kwargs):
    """Takes a list of objects and returns only those where each **kwargs
    matches the attributes exactly.
    """
    if not kwargs:
        return args
    ret = []
    add_arg = True
    for arg in args:
        for attr, attr_vals in kwargs.items():
            if not isinstance(attr_vals, list):
                attr_vals = [attr_vals]

            #logging.debug("arg=%s getattr=%s attr=%s attr_vals=%s", arg,
            #              getattr(arg, attr), attr, attr_vals)
            if getattr(arg, attr) not in attr_vals:
                add_arg = False
                break
        #logging.debug("add_arg=%s", add_arg)
        if add_arg:
            ret.append(arg)
        else:
            add_arg = True
    return ret

    #return [arg for arg in args if
    #        all(
    #            [getattr(arg, k) == v for k, v in kwargs.items()]
    #        )]


class QuerySet(object):
    """QuerySet for object objects
    """
    _base_filter = None
    _lazy = None
    _objects = None

    @property
    def objects(self):
        ret = None
        if isinstance(self._objects, list):
            ret = copy(self._objects)
        if not ret:
            ret = self._get_objects_wrap()
        return ret

    def _get_objects_wrap(self):
        objects = self._get_objects()
        if isinstance(self._objects, list):
            self._objects = objects
        return objects

    def _get_objects(self):
        """This method gets overridden to specify how to get the list of objects
        """
        return super(QuerySet, self)._get_objects()

    def __init__(self, objects=None, base_filter=None, base_filter_replace=False):
        if objects:
            self._objects = objects
        if base_filter:
            if base_filter_replace:
                self._base_filter = base_filter
            else:
                if not self._base_filter:
                    self._base_filter = {}
                self._base_filter.update(base_filter)

    def all(self):
        return self.filter()

    def filter(self, **kwargs):
        if self._base_filter:
            kwargs.update(self._base_filter)
        return filter_by_attrs(self, **kwargs)

    def __setitem__(self, k, v):
        self.objects[k] = v

    def append(self, v):
        self.objects.append(v)

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.objects.__repr__())

    def __len__(self):
        return len(self.objects)

    def __getitem__(self, key):
        return self.objects[key]

    def __delitem__(self, key):
        del self.objects[key]

    def __iter__(self):
        return iter(self.objects)

    def __reversed__(self):
        return reversed(self.objects)
