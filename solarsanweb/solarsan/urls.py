
from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView
#from polls.models import Poll

urlpatterns = patterns('solarsan.views',
    # Non-generic views
    url(r'^(?:status)?$', 'status'),
    url(r'^graph/stats.json', 'graph_stats_json'),
#    url(r'^graph/utilization.json$', 'graph_utilization'),
#    url(r'^graph/utilization.json$', 'graph_iops'),
#    url(r'^graph/ajax/utilization.json$', 'graph_utilization_ajax'),
#    url(r'^graph/iops.json$', 'graph_iops'),
#    url(r'^graph/throughput.json$', 'graph_throughput'),
    
#    url(r'^(?P<poll_id>\d+)/$', 'detail'),
#    url(r'^(?P<poll_id>\d+)/results/$', 'results'),
#    url(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
        
    # Generic views
#    url(r'^$',
#        ListView.as_view(
#            queryset=Poll.objects.order_by('-pub_date')[:5],
#            context_object_name='latest_poll_list',
#            # By default, the ListView generic view uses a default template called <app name>/<model name>_list.html;
#            template_name='polls/index.html')),
#    url(r'^(?P<pk>\d+)/$',
#        DetailView.as_view(
#            model=Poll,
#            # By default, the DetailView generic view uses a template called <app name>/<model name>_detail.html
#            template_name='polls/detail.html')),
#    url(r'^(?P<pk>\d+)/results/$',
#        DetailView.as_view(
#            model=Poll,
#            template_name='polls/results.html'),
#        name='poll_results'),
#    url(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
)

#urlpatterns += patterns('solarsan.ajax',
#    url(r'^graph/stats.json', 'graph_stats'),
#)

