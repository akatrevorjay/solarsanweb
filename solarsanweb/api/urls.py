from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
import cluster.urls


urlpatterns = patterns(
    'api.views',
    url(r'^$', 'api_root'),

    #url(r'^users/$', views.UserList.as_view(), name='user-list'),
    #url(r'^users/(?P<pk>\d+)/$', views.UserDetail.as_view(), name='user-detail'),

    url(r'^users/$', views.UserList2.as_view(), name='user-list'),
    url(r'^users/(?P<pk>\d+)/$', views.UserInstance2.as_view(), name='user-detail'),

    url(r'^groups/$', views.GroupList.as_view(), name='group-list'),
    url(r'^groups/(?P<pk>\d+)/$', views.GroupDetail.as_view(), name='group-detail'),

    url(r'^pools/$', views.pool_list, name='pool-list'),
    #url(r'^pools/$', views.PoolList.as_view(), name='pool-list'),
    url(r'^pools/(?P<pk>\d+)/$', views.PoolDetail.as_view(), name='pool-detail'),

    ##url(r'^snippets/$', views.SnippetList3.as_view(), name='snippet-list'),
    ##url(r'^snippets/(?P<pk>[0-9]+)/$', views.SnippetDetail3.as_view(), name='snippet-detail'),
    ##url(r'^snippets/(?P<pk>[0-9]+)/highlight/$', views.SnippetHighlight.as_view(), name='snippet-highlight'),

    #url(r'^snippets/$',
    #    views.SnippetList3.as_view(),
    #    name='snippet-list'),
    #url(r'^snippets/(?P<pk>[0-9]+)/$',
    #    views.SnippetDetail3.as_view(),
    #    name='snippet-detail'),
    #url(r'^snippets/(?P<pk>[0-9]+)/highlight/$',
    #    views.SnippetHighlight.as_view(),
    #    name='snippet-highlight'),

)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'jsonp', 'api', 'xml', 'yaml', 'html'])

urlpatterns += patterns(
    '',
    url(r'^cluster/', include(cluster.urls.api_patterns)),
)

# Default login/logout views
#urlpatterns += patterns(
#    '',
#    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
#)
