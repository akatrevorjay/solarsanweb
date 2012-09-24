from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

#from storage.models import zPool, zDataset
from storage.models import Pool, Dataset, Filesystem, Snapshot
import zfs as z

import mongogeneric


"""
Testing mongo to zfs bridge, scrapped but good example to override generic views
"""

class ZfsSingleDocumentMixIn(mongogeneric.SingleDocumentMixin):
    #zfs_obj = None

    #def get_context_data(self, **kwargs):
    #    ctx = super(ZfsSingleDocumentMixIn, self).get_context_data(**kwargs)
    #    ctx_obj_name = self.context_object_name
    #    ctx['zfs_'+ctx_obj_name] = self.zfs_obj(ctx[ctx_obj_name])
    #    return ctx

    #def get_queryset(self):
    #    """
    #    Get the queryset to look an object up against. May not be called if
    #    `get_object` is overridden.
    #    """
    #    if self.queryset is None:
    #        if self.zfs_obj:
    #            return self.zfs_obj.dbm.objects()
    #        else:
    #            return super(ZfsSingleDocumentMixIn, self).get_queryset()
    #    return self.queryset.clone()
    pass

class ZfsBaseDetailView(mongogeneric.BaseDetailView, ZfsSingleDocumentMixIn, mongogeneric.View):
    pass

class ZfsDetailView(mongogeneric.SingleDocumentTemplateResponseMixin, ZfsBaseDetailView):
    """
    Render a "detail" view of an object.

    By default this is a document instance looked up from `self.queryset`, but the
    view will support display of *any* object by overriding `self.get_object()`.
    """


"""
Pools
"""

class PoolView(object):
    document = Pool
    slug_field = 'name'
    context_object_name = 'pool'

## TODO Create/Destroy

class PoolHealthDetailView(PoolView, ZfsDetailView):
    template_name = 'storage/pool_health.html'
    def get_context_data(self, **kwargs):
        ctx = super(PoolHealthDetailView, self).get_context_data(**kwargs)

        ctx_obj_name = self.context_object_name
        obj = ctx[ctx_obj_name]
        zobj = ctx[ctx_obj_name] = self.zfs_obj(obj.name)

        ctx['dataset'] = zobj.filesystem

        return ctx

class PoolAnalyticsDetailView(PoolView, ZfsDetailView):
    template_name = 'storage/pool_analytics.html'
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        return ctx

"""
Datasets
"""

class DatasetView(object):
    document = Filesystem
    slug_field = 'name'
    context_object_name = 'dataset'
    def get_context_data(self, **kwargs):
        try:
            ctx = super(DatasetView, self).get_context_data(**kwargs)
        except:
            ctx = {}
        ctx['pool'] = ctx['dataset'].pool
        return ctx

#class DatasetListView(DatasetView, mongogeneric.ListView):
#    context_object_name = 'datasets'
#    template_name = 'solarsan/dataset_list.html'

#class DatasetCreateView(DatasetView, mongogeneric.DetailView):
#    pass

#class DatasetDeleteView(DatasetView, mongogeneric.DetailView):
#    pass

class DatasetHealthDetailView(DatasetView, mongogeneric.DetailView):
    template_name = 'storage/dataset_health.html'
    pass

class DatasetSnapshotsView(DatasetView, mongogeneric.DetailView):
    template_name = 'storage/dataset_snapshots.html'
    pass


"""
Volumes
  >> LIO target management for volumes
"""
import rtslib
#root = rtslib.root

#from storage.models import Target
class Target(object):
    pass

class TargetView(object):
    model = Target
    slug_field = "name"
    context_object_name = 'target'

class TargetACLsView(TargetView, generic.DetailView):
    template_name = 'storage/target_acls_detail.html'

class TargetLunsView(TargetView, generic.DetailView):
    template_name = 'storage/target_luns_detail.html'





