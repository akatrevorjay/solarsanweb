
from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    'status.views',
    url(r'^$', 'index', name='index'),
    url(r'^$', 'index', name='status'),

    url(r'^reboot$', 'reboot', name='reboot'),
    url(r'^shutdown$', 'shutdown', name='shutdown'),
)

#urlpatterns += patterns('solarsan.ajax',
#    url(r'^graph/stats.json', 'graph_stats'),
#url(r'^$',
#    ListView.as_view(
#        queryset=Poll.objects.order_by('-pub_date')[:5],
#        context_object_name='latest_poll_list',
#        # By default, the ListView generic view uses a default template called <app name>/<model name>_list.html;
#        template_name='polls/index.html')),
#url(r'^(?P<pk>\d+)/$',
#    DetailView.as_view(
#        model=Poll,
#        # By default, the DetailView generic view uses a template called <app name>/<model name>_detail.html
#        template_name='polls/detail.html')),
#url(r'^(?P<pk>\d+)/results/$',
#    DetailView.as_view(
#        model=Poll,
#        template_name='polls/results.html'),
#    name='poll_results'),
#url(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
#)

