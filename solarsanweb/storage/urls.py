
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import storage.views
#from solarsan.models import Pool, Dataset, Snapshot

urlpatterns = patterns('storage.views',
    (r'^pools/health/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolHealthDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolAnalyticsDetailView.as_view()),
    (r'^pools/detail/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolDetailView.as_view()),

    (r'^datasets/detail/(?P<slug>[A-z0-9_\-/]+)$', storage.views.DatasetDetailView.as_view()),
    (r'^datasets/health/(?P<slug>[A-z0-9_\-/]+)$', storage.views.DatasetHealthDetailView.as_view()),
    (r'^datasets/snapshots/(?P<slug>[A-z0-9_\-/]+)$', storage.views.DatasetSnapshotsView.as_view()),
)

