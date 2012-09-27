from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from datetime import timedelta
import json

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

        #ctx_obj_name = self.context_object_name
        #obj = ctx[ctx_obj_name]
        #zobj = ctx[ctx_obj_name] = self.zfs_obj(obj.name)
        #ctx['dataset'] = obj.filesystem

        return ctx


from analytics.views import time_window_list
import logging


class PoolAnalyticsDetailView(PoolView, ZfsDetailView):
    template_name = 'storage/pool_analytics.html'
    charts = ['iops', 'bandwidth', 'usage']
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        obj = kwargs['object']
        time_window = int( kwargs.get( 'time_window', 86400 ) );
        if not time_window in time_window_list:
            raise http.Http404
        name = kwargs.get( 'name', 'iops' )
        if not name in self.charts:
            raise http.Http404

        ctx.update({'title': 'Analytics',
                    'graph_list': self.charts,
                    'time_window': time_window,
                    'time_window_list': time_window_list,

                    'graph': name, })
        return ctx
    def get(self, request, **kwargs):
        self.object = self.get_object()
        kwargs.update({'request': request,
                       'object': self.object, })
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class JSONMixIn(object):
    def get(self, request, **kwargs):
        self.object = self.get_object()
        kwargs.update({'request': request,
                       'object': self.object, })
        context = self.get_context_data(**kwargs)
        ret = self.get_json_data(**kwargs)
        return http.HttpResponse(json.dumps(ret),
                                  mimetype="application/json", )

class PoolAnalyticsRenderView(JSONMixIn, PoolAnalyticsDetailView):
    def get_json_data(self, **kwargs):
        ctx = self.get_context_data(**kwargs)
        obj = kwargs['object']
        render_func = getattr(obj.analytics, ctx['graph'])
        kwargs['start'] = kwargs['request'].GET.get('start')
        kwargs['format'] = 'nvd3'
        ret = render_func(**kwargs)
        return ret


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





