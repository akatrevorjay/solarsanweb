
from django.conf.urls.defaults import patterns, url, include
from django.views import generic
from . import views

peers_patterns = patterns(
    'cluster.views',
    url(r'^$',
        'peer_list',
        name='peer-list'),
    url(r'^/detail/(?P<peer>.+)$',
        'peer_detail',
        name='peer'),
)

urlpatterns = patterns(
    'cluster.views',
    url(r'^$', 'home', name='cluster'),

    url(r'^peers/$', include(peers_patterns)),
)

