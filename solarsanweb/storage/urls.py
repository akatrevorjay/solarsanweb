
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import pools.views
from solarsan.models import Pool

urlpatterns = patterns('pools.views',
    (r'^pools/health/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolHealthDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolAnalyticsDetailView.as_view()),
    (r'^pools/detail/(?P<slug>[A-z0-9_\-]+)$', pools.views.PoolDetailView.as_view()),
    
    (r'^datasets/detail/(?P<slug>[A-z0-9_\-/]+)$', pools.views.DatasetDetailView.as_view()),
    (r'^datasets/health/(?P<slug>[A-z0-9_\-/]+)$', pools.views.DatasetHealthDetailView.as_view()),
    (r'^datasets/snapshots/(?P<slug>[A-z0-9_\-/]+)$', pools.views.DatasetSnapshotsView.as_view()),
)

