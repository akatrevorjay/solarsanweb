
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import pools.views
from solarsan.models import Pool

urlpatterns = patterns('pools.views',
    (r'^health/(?P<slug>[A-z0-9_\-/]+)$', datasets.views.DatasetHealthDetailView.as_view()),
    (r'^health/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolHealthDetailView.as_view()),
    (r'^analytics/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolAnalyticsDetailView.as_view()),

    (r'^detail/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolDetailView.as_view()),
    (r'^dataset/detail/(?P<slug>[A-z0-9_\-/]+)$', pools.views.DatasetDetailView.as_view()),
    (r'^dataset/snapshots/(?P<slug>[A-z0-9_\-/]+)$', pools.views.DatasetSnapshotsView.as_view()),
)

