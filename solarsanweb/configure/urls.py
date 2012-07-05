
from django.conf.urls.defaults import patterns, url, include
from django.views import generic
from configure.views import *

urlpatterns = patterns('configure.views',
    (r'^$', HomeListView.as_view()),
    (r'^network$', NetworkDetailView.as_view()),
    (r'^network/interfaces$', NetworkInterfaceListView.as_view(), {}, 'network-interface-list'),
    (r'^network/interfaces/detail/(?P<interface>(eth|ib)\d+)$', NetworkInterfaceDetailView.as_view()),

    #url(r'network/interfaces/add$', NetworkInterfaceConfigCreate.as_view(), name='network-interface-add'),
    url(r'network/interfaces/(?P<slug>(eth|ib)\d+)$', NetworkInterfaceConfigUpdate.as_view(), name='network-interface-update'),
    url(r'network/interfaces/(?P<slug>(eth|ib)\d+)/delete$', NetworkInterfaceConfigDelete.as_view(), name='network-interface-delete'),

    (r'^cluster/peers$', ClusterPeerListView.as_view()),
    (r'^cluster/peers/detail/(?P<peer>.+)$', ClusterPeerDetailView.as_view()),
)

