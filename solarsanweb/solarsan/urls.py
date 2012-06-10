
from django.conf.urls import patterns, url, include
from django.views.generic import DetailView, ListView

from solarsan.models import Pool

urlpatterns = patterns('solarsan.views',
    (r'^(?:status)?$', 'status'),

    (r'^status/pool/(?P<pool>.+)$', 'status_pool'),

    (r'^status/dataset/(?P<dataset>.+)$', 'status_dataset'),
    (r'^status/dataset_(?P<action>[^/]+)/(?P<dataset>.+)/$', 'status_dataset_action'),

    (r'^scheduler$', 'scheduler'),

    (r'^graphs$', 'graphs'),

    #(r'^pools/(?P<pool_name>\d+)/$',
    #    DetailView.as_view(
    #        context_object_name='pool_detail',
    #        model=Pool,
    #    )),

    #(r'^pool/(?P<pk>\d+)/datasets$',
    #    DetailView.as_view(
    #        model=Pool,
    #    ),
    #    name='pool_datasets'),
    #(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
)

#urlpatterns += patterns('solarsan.ajax',
#    (r'^graph/stats.json', 'graph_stats'),
#)

