#from django.shortcuts import render_to_response, get_object_or_404
#from django.template import RequestContext
#from django.contrib.auth.decorators import login_required
#from django.utils.decorators import method_decorator
#from django.views.decorators.csrf import csrf_exempt
#from django.views.decorators.cache import cache_page
#from django.core.cache import cache
from django import http
from django.views import generic

#from datetime import timedelta
import mongogeneric
import logging

from solarsan.views import JsonMixIn, KwargsMixIn
from storage.models import Pool, Dataset, Filesystem, Snapshot, Volume
from analytics.views import time_window_list
import storage.target

"""
Pools
"""

class PoolView(object):
    document = Pool
    slug_field = 'name'
    context_object_name = 'pool'


class PoolHealthDetailView(PoolView, KwargsMixIn, mongogeneric.DetailView):
    template_name = 'storage/pool_health.html'


class PoolAnalyticsDetailView(PoolView, KwargsMixIn, mongogeneric.DetailView):
    template_name = 'storage/pool_analytics.html'
    charts = ['iops', 'bandwidth', 'usage']
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        obj = self.object
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


class PoolAnalyticsRenderView(JsonMixIn, PoolAnalyticsDetailView):
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
        ctx['pool'] = ctx[self.context_object_name].pool
        return ctx

#class DatasetListView(DatasetView, mongogeneric.ListView):
#    context_object_name = 'datasets'
#    template_name = 'solarsan/dataset_list.html'

#class DatasetCreateView(DatasetView, mongogeneric.DetailView):
#    pass

#class DatasetDeleteView(DatasetView, mongogeneric.DetailView):
#    pass

class DatasetHealthDetailView(object):
    template_name = 'storage/dataset_health.html'
    pass

class DatasetSnapshotsView(object):
    template_name = 'storage/dataset_snapshots.html'
    pass


"""
Filesystem
"""


class FilesystemView(DatasetView):
    document = Filesystem
    context_object_name = 'filesystem'


class FilesystemHealthDetailView(FilesystemView, DatasetHealthDetailView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_health.html'
    pass


class FilesystemSnapshotsView(FilesystemView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_snapshots.html'
    pass


"""
Volumes
"""


class VolumeView(DatasetView):
    document = Volume


class VolumeHealthDetailView(VolumeView, DatasetHealthDetailView, mongogeneric.DetailView):
    template_name = 'storage/volume_health.html'

    def get_context_data(self, **kwargs):
        context = super(VolumeHealthDetailView, self).get_context_data(**kwargs)
        #context['targets'] = storage.target.list(fabric_module=fabric)
        targets = context['targets'] = storage.target.list(cached=True)
        return context


class VolumeSnapshotsView(VolumeView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/volume_snapshots.html'
    pass


"""
Targets
"""

fabric = storage.target.get_fabric_module('iscsi')

a = mongogeneric.DetailView


class TargetDetailView(KwargsMixIn, generic.DetailView):
    template_name = 'storage/target_detail.html'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = storage.target.get(wwn=slug, cached=True)
        except storage.target.DoesNotExist:
            raise http.Http404

        targets = self.targets = storage.target.list(cached=True)

        target = None
        for t in targets:
            if t.wwn == slug:
                target = t
        if not target:
            raise http.Http404

        return target

    def get_context_data(self, **kwargs):
        context = super(VolumeHealthDetailView, self).get_context_data(**kwargs)
        #context['targets'] = storage.target.list(fabric_module=fabric)
        targets = context['targets'] = storage.target.list(cached=True)
        return context

