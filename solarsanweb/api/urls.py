from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from api import views


urlpatterns = patterns(
    'api.views',
    url(r'^$', 'api_root'),

    #url(r'^users/$', views.UserList.as_view(), name='user-list'),
    #url(r'^users/(?P<pk>\d+)/$', views.UserDetail.as_view(), name='user-detail'),

    url(r'^users/$', views.UserList2.as_view(), name='user-list'),
    url(r'^users/(?P<pk>\d+)/$', views.UserInstance2.as_view(), name='user-detail'),

    url(r'^groups/$', views.GroupList.as_view(), name='group-list'),
    url(r'^groups/(?P<pk>\d+)/$', views.GroupDetail.as_view(), name='group-detail'),

    url(r'^cluster/probe/$', views.cluster_probe, name='cluster-probe'),

    url(r'^pools/$', views.pool_list, name='pool-list'),
    #url(r'^pools/$', views.PoolList.as_view(), name='pool-list'),
    url(r'^pools/(?P<pk>\d+)/$', views.PoolDetail.as_view(), name='pool-detail'),

    #url(r'^recipient_groups/$', views.RecipientGroupList.as_view(), name='recipient_group-list'),
    #url(r'^recipient_groups/(?P<pk>\d+)/$', views.RecipientGroupDetail.as_view(), name='recipient_group-detail'),

    ##url(r'^recipients/$', views.RecipientGroup.as_view(), name='recipient-list'),
    ##url(r'^recipients/(?P<pk>\d+)/$', views.RecipientDetail.as_view(), name='recipient-detail'),

    #url(r'^campaigns/$', views.CampaignList.as_view(), name='campaign-list'),
    #url(r'^campaigns/(?P<pk>\d+)/$', views.CampaignDetail.as_view(), name='campaign-detail'),
    ##url(r'^campaigns/(?P<pk>\d+)/start$', views.CampaignStart.as_view(), name='campaign-start'),
    ##url(r'^campaigns/(?P<pk>\d+)/pause$', views.CampaignPause.as_view(), name='campaign-pause'),

    #url(r'^templates/$', views.TemplateList.as_view(), name='template-list'),
    #url(r'^templates/(?P<pk>\d+)/$', views.TemplateDetail.as_view(), name='template-detail'),

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

# Default login/logout views
urlpatterns += patterns(
    '',
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
