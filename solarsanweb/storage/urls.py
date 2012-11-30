
from django.conf.urls import patterns, url, include
#from django.views import generic
import storage.views

from .api import PoolResource
pool_resource = PoolResource()

from solarsan.debug import start_debug
start_debug()

pool_analytics_patterns = patterns(
    'storage.views',
    url(r'^$',
        'pool_analytics',
        name='pool-analytics'),
    url(r'^render$',
        'pool_analytics_render',
        name='pool-analytics-render'),
)

pool_patterns = patterns(
    'storage.views',
    url(r'^$', 'pool_health', name='pool'),
    #url(r'^/delete$', 'pool_remove', name='pool-remove'),
    url(r'^health/', 'pool_health', name='pool-health'),
    url(r'^analytics/', include(pool_analytics_patterns)),
    url(r'^analytics/(?P<name>[\w_]+)(?:/(?P<time_window>\d+))?/',
        include(pool_analytics_patterns)),
)


filesystem_patterns = patterns(
    'storage.views',
    url(r'^$', 'filesystem_health', name='filesystem'),
    url(r'^/delete$', 'filesystem_remove', name='filesystem-remove'),
    url(r'^health$', 'filesystem_health', name='filesystem-health'),
    url(r'^snapshots$', 'filesystem_snapshots', name='filesystem-snapshots'),
)

volume_patterns = patterns(
    'storage.views',
    url(r'^$', 'volume_health', name='volume'),
    url(r'^/delete$', 'volume_remove', name='volume-remove'),
    url(r'^health$', 'volume_health', name='volume-health'),
    url(r'^snapshots$', 'volume_snapshots', name='volume-snapshots'),
)

target_patterns = patterns(
    'storage.views',
    url(r'^$', 'target_detail', name='target'),
    url(r'^/delete$', 'target_remove', name='target-remove'),
    url(r'pg_create$',
        'target_pg_create',
        name='target-pg-create'),
    url(r'pg_lun_map$',
        'target_pg_volume_lun_map',
        name='target-pg-volume-lun-map'),
    url(r'pg/(?P<tag>\d+)$',
        'target_pg_update',
        name='target-pg-update'),
)

urlpatterns = patterns(
    'storage.views',
    url(r'^pool/create', 'pool_create_wizard', name='pool-create'),
    url(r'^pools/(?P<slug>[\w]+)/', include(pool_patterns)),

    url(r'^filesystem/create', 'filesystem_create', name='filesystem-create'),
    url(r'^filesystem/(?P<slug>[\w\/\-\.]+)/', include(filesystem_patterns)),

    url(r'^volume/create', 'volume_create', name='volume-create'),
    url(r'^volumes/(?P<slug>[\w\/\-\.]+)/', include(volume_patterns)),

    url(r'^target/create', 'target_create', name='target-create'),
    url(r'^targets/(?P<slug>[\w\/\-\.]+:[\w\.]+)/', include(target_patterns)),

    url(r'^api/', include(pool_resource.urls), name='storage-api'),
)

