
from django.conf.urls.defaults import patterns, url, include
from django.views import generic
import views
#from configure.views import *

urlpatterns = patterns('configure.views',
    (r'^$', views.HomeListView.as_view()),
    
    #(r'^network$', NetworkDetailView.as_view()),
    
    (r'^network/interfaces$', views.NetworkInterfaceListView.as_view(), {}, 'network-interface-list'),
    url(r'network/interfaces/(?P<slug>(eth|ib)\d)$', views.network_interface_config, name='network-interface-update'),

    #(r'^network/interfaces/detail/(?P<interface>(eth|ib)\d+)$', NetworkInterfaceDetailView.as_view()),
    #url(r'network/interfaces/add$', NetworkInterfaceConfigCreate.as_view(), name='network-interface-add'),
    #url(r'network/interfaces/config/(?P<slug>(eth|ib)\d+)$', NetworkInterfaceConfigUpdate.as_view(), name='network-interface-config-update'),
    #url(r'network/interfaces/config/(?P<slug>(eth|ib)\d+)/delete$', NetworkInterfaceConfigDelete.as_view(), name='network-interface-config-delete'),

    (r'^cluster/peers$', views.ClusterPeerListView.as_view()),
    (r'^cluster/peers/detail/(?P<peer>.+)$', views.ClusterPeerDetailView.as_view()),
)

