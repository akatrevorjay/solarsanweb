from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from solarsan.models import Pool, Dataset, Filesystem, Snapshot
import zfs

"""
Pools
"""

class PoolView(object):
    model = Pool
    slug_field = 'name'
    context_object_name = 'pool'

class PoolDetailView(PoolView, generic.DetailView):
    template_name = 'pools/pool_detail.html'
    pass

## TODO Create/Destroy

class PoolHealthDetailView(PoolView, generic.DetailView):
    template_name = 'pools/pool_health.html'
    def get_context_data(self, **kwargs):
        ctx = super(PoolHealthDetailView, self).get_context_data(**kwargs)
        ctx['dataset'] = ctx['pool'].filesystem
        return ctx

class PoolAnalyticsDetailView(PoolView, generic.DetailView):
    template_name = 'pools/pool_analytics.html'
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        return ctx

"""
Datasets
"""

class DatasetView(object):
    model = Filesystem
    slug_field = 'name'
    context_object_name = 'dataset'

#class DatasetListView(DatasetView, generic.ListView):
#    context_object_name = 'datasets'
#    template_name = 'solarsan/dataset_list.html'

class DatasetDetailView(DatasetView, generic.DetailView):
    template_name = 'pools/dataset_detail.html'

#class DatasetCreateView(DatasetView, generic.DetailView):
#    pass

#class DatasetDeleteView(DatasetView, generic.DetailView):
#    pass

class DatasetHealthDetailView(DatasetView, generic.DetailView):
    template_name = 'pools/dataset_health.html'
    def get_context_data(self, **kwargs):
        ctx = super(DatasetHealthDetailView, self).get_context_data(**kwargs)
        ctx['pool'] = ctx['dataset'].pool
        return ctx

class DatasetSnapshotsView(DatasetView, generic.DetailView):
    template_name = 'pools/dataset_snapshots.html'

