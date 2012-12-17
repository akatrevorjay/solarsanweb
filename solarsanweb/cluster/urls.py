
from django.conf.urls.defaults import patterns, url, include
from django.views import generic
from rest_framework.urlpatterns import format_suffix_patterns
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

# API
api_patterns = patterns(
    'cluster.views',
    url(r'^probe/$', 'cluster_probe', name='cluster-probe'),
    url(r'^ping/$', 'cluster_ping', name='cluster-ping'),
)
# Format suffixes
api_patterns = format_suffix_patterns(api_patterns, allowed=['json', 'jsonp', 'api', 'xml', 'yaml', 'html'])

urlpatterns = patterns(
    'cluster.views',
    url(r'^$', 'home', name='cluster'),

    url(r'^peers/$', include(peers_patterns)),

    #url(r'^api/v1/', include(api_patterns)),
)

