
from django.conf.urls import patterns, url, include
#from django.views import generic

from .api import PoolResource
pool_resource = PoolResource()

from solarsan.debug import start_debug
start_debug()

re_storage_object = '[\w\d_\-/\.:]+'


pool_analytics_patterns = patterns('storage.views',
    url(r'^$',
        'pool_analytics',
        name='pool-analytics'),
    url(r'^render$',
        'pool_analytics_render',
        name='pool-analytics-render'),
)

pool_patterns = patterns('storage.views',
    url(r'^$', 'pool_health', name='pool'),
    url(r'^health/', 'pool_health', name='pool-health'),
    url(r'^analytics/', include(pool_analytics_patterns)),
    url(r'^analytics/(?P<name>[\w_]+)(?:/(?P<time_window>\d+))?/',
        include(pool_analytics_patterns)),
)


filesystem_patterns = patterns('storage.views',
    url(r'^$', 'filesystem_health', name='filesystem'),
    url(r'^health$', 'filesystem_health', name='filesystem-health'),
    url(r'^snapshots$', 'filesystem_snapshots', name='filesystem-snapshots'),
)

volume_patterns = patterns('storage.views',
    url(r'^$', 'volume_health', name='volume'),
    url(r'^health$', 'volume_health', name='volume-health'),
    url(r'^snapshots$', 'volume_snapshots', name='volume-snapshots'),
)

target_patterns = patterns('storage.views',
    url(r'^$', 'target_detail', name='target'),
    url(r'^tpg/(?P<tag>\d)/update$',
        'target_tpg_update',
        name='target_tpg_update'),
)

urlpatterns = patterns('storage.views',
    url(r'^pools/(?P<slug>[A-z0-9]+)/', include(pool_patterns)),
    url(r'^filesystem/(?P<slug>[A-z0-9\/\-\.]+)/', include(filesystem_patterns)),
    url(r'^volumes/(?P<slug>[A-z0-9\/\-\.]+)/', include(volume_patterns)),
    url(r'^targets/(?P<slug>[A-z0-9\/\-\.:]+)/', include(target_patterns)),

    url(r'^api/', include(pool_resource.urls), name='storage-api'),
)

