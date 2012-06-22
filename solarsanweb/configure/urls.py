
from django.conf.urls.defaults import patterns, url, include
from django.views import generic

import configure.views
from solarsan.models import Pool

urlpatterns = patterns('configure.views',
    (r'^$', configure.views.HomeListView.as_view()),
    (r'^network$', configure.views.NetworkDetailView.as_view()),
    (r'^network/interfaces/detail/(?P<interface>\w+)$', configure.views.NetworkInterfaceDetailView.as_view()),

    (r'^cluster/peers$', configure.views.ClusterPeerListView.as_view()),
    (r'^cluster/peers/detail/(?P<peer>.+)$', configure.views.ClusterPeerDetailView.as_view()),
)

