from django.conf.urls.defaults import patterns, url, include
from logs.views import LogTailView, LogListView
from django.views.generic import DetailView, ListView

urlpatterns = patterns('logs.views',
    url(r'^(?:home)?$',
     LogListView.as_view(),
     name='log_list' ),

    url(r'^nab/(?P<logfile>[-\w\.]+)/$',
     LogTailView.as_view(),
     name='log_tail' ),

    url(r'^nab/(?P<logfile>[-\w\.]+)/(?P<seek_to>\d+)/$',
     LogTailView.as_view(),
     name='log_seek' ),
)

#urlpatterns += patterns('solarsan.ajax',
#    (r'^graph/stats.json', 'graph_stats'),
#)

