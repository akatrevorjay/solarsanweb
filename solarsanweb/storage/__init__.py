
import rtslib
import models


def _patch_rtslib():
    """ Monkeypatch RTSLib """
    # StorageObject
    cls = rtslib.tcm.StorageObject
    if not getattr(cls, 'get_volume', None):
        def get_volume(self):
            """ Get Storage Volume for this object """
            return models.Volume.objects.get(backstore_wwn=self.wwn)
        setattr(cls, 'get_volume', get_volume)

    # Target
    cls = rtslib.target.Target
    if not getattr(cls, 'short_wwn', None):
        def short_wwn(arg):
            """ Shorten WWN string """
            if not isinstance(arg, basestring):
                arg = arg.wwn
            return arg.split(':', 2)[1]
        setattr(cls, 'short_wwn', short_wwn)

        setattr(cls, 'type', 'target')

_patch_rtslib()
