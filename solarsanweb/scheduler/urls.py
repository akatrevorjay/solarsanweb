
from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView

urlpatterns = patterns('scheduler.views',
    # Non-generic views
    url(r'^(?:home)?$', 'home'),

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
)

#urlpatterns += patterns('solarsan.ajax',
#    url(r'^graph/stats.json', 'graph_stats'),
#)

