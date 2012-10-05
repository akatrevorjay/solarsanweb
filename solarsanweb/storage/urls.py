
from django.conf.urls import patterns, url, include
#from django.views import generic

from .api import PoolResource
pool_resource = PoolResource()

from solarsan.debug import start_debug
start_debug()

re_storage_object = '[\w\d_\-/\.:]+'


pool_analytics_patterns = patterns('storage.views',
    url(r'^(?:/(?P<name>[\w\d_\-]+))?(?:/(?P<time_window>\d+))?$',
        'pool_analytics',
        name='pool-analytics'),
    url(r'^(?:/(?P<name>[\w\d_\-]+))?(?:/(?P<time_window>\d+))?/render$',
        'pool_analytics_render',
        name='pool-analytics-render'),
)

pool_patterns = patterns('storage.views',
    url(r'^$', 'pool_health', name='pool'),
    url(r'^health/', 'pool_health', name='pool-health'),
    url(r'^analytics/', include(pool_analytics_patterns)),
)

urlpatterns = patterns('storage.views',
    url(r'^pools/(?P<slug>[A-z0-9]+)/', include(pool_patterns)),

    url(r'^filesystems/(?P<slug>%s)$' % re_storage_object,
        'filesystem_health',
        name='filesystem-health'),
    url(r'^filesystems/(?P<slug>%s)/snapshots$' % re_storage_object,
        'filesystem_snapshots',
        name='filesystem-snapshots'),

    url(r'^volumes/(?P<slug>%s)$' % re_storage_object,
        'volume_health',
        name='volume-health'),
    url(r'^volumes/(?P<slug>%s)/snapshots$' % re_storage_object,
        'volume_snapshots',
        name='volume-snapshots'),


    url(r'^targets/(?P<slug>%s)/$' % re_storage_object,
        'target_detail',
        name='target'),
    url(r'^targets/(?P<slug>%s)/tpg/(?P<tag>\d)/update$' % re_storage_object,
        'target_tpg_update',
        name='target-tpg-update'),

    # API
    url(r'^api/', include(pool_resource.urls), name='storage-api'),
)

