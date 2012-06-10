
from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView

from solarsan.models import Pool

urlpatterns = patterns('pools.views',
    (r'^$', ListView.as_view(
        model=Pool,
        context_object_name='pool_list',
        )),

    (r'^detail/(?P<slug>[A-z0-9_-]+)$', DetailView.as_view(
        model=Pool,
        context_object_name='pool_detail',
        slug_field='name',
        )),

    (r'^health/(?P<slug>[A-z0-9_-]+)$', DetailView.as_view(
        model=Pool,
        context_object_name='pool_health',
        slug_field='name',
        template_name='solarsan/pool_health.html',
        )),

    (r'^analytics/(?P<slug>[A-z0-9_-]+)$', DetailView.as_view(
        model=Pool,
        context_object_name='pool_analytics',
        slug_field='name',
        template_name='solarsan/pool_analytics.html',
        )),
)

