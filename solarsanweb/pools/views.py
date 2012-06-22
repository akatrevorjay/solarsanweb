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
        ctx['something_else'] = None  # add something to ctx
        return ctx

