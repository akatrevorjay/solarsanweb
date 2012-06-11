
from django.conf.urls import patterns, url, include
from django.views.generic import DetailView, ListView

import datasets.views

urlpatterns = patterns('datasets.views',
    #(r'^$', pools.views.PoolListView.as_view()),
    (r'^detail/(?P<slug>[A-z0-9_\-/]+)$', datasets.views.DatasetDetailView.as_view()),
    (r'^snapshots/(?P<slug>[A-z0-9_\-/]+)$', datasets.views.DatasetSnapshotsView.as_view()),
    (r'^health/(?P<slug>[A-z0-9_\-/]+)$', datasets.views.DatasetHealthDetailView.as_view()),
)

