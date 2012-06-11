
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import cluster.views
from solarsan.models import Pool

urlpatterns = patterns('cluster.views',
    (r'^$', cluster.views.PeerListView.as_view()),
    (r'^peers$', cluster.views.PeerListView.as_view()),
    (r'^peers/detail/(?P<peer>.+)$', cluster.views.PeerDetailView.as_view()),
)

