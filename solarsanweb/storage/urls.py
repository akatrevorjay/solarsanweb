
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import storage.views
#from storage.models import Pool, Filesystem, Snapshot

urlpatterns = patterns('storage.views',
    (r'^pools/detail/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolHealthDetailView.as_view()),
    (r'^pools/health/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolHealthDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)$', storage.views.PoolAnalyticsDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)/render$', storage.views.PoolAnalyticsRenderView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)/(?P<name>[A-z0-9_\-]+)$', storage.views.PoolAnalyticsDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)/(?P<name>[A-z0-9_\-]+)/render$', storage.views.PoolAnalyticsRenderView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)/(?P<name>[A-z0-9_\-]+)/(?P<time_window>[0-9]+)$', storage.views.PoolAnalyticsDetailView.as_view()),
    (r'^pools/analytics/(?P<slug>[A-z0-9_\-]+)/(?P<name>[A-z0-9_\-]+)/(?P<time_window>[0-9]+)/render$', storage.views.PoolAnalyticsRenderView.as_view()),

    (r'^volumes/detail/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.VolumeHealthDetailView.as_view()),
    (r'^volumes/health/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.VolumeHealthDetailView.as_view()),
    (r'^volumes/snapshots/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.VolumeSnapshotsView.as_view()),

    (r'^filesystems/detail/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.FilesystemHealthDetailView.as_view()),
    (r'^filesystems/health/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.FilesystemHealthDetailView.as_view()),
    (r'^filesystems/snapshots/(?P<slug>[A-z0-9_\-/\.]+)$', storage.views.FilesystemSnapshotsView.as_view()),
)

