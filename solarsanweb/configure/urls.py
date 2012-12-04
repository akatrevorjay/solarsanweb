
from django.conf.urls.defaults import patterns, url, include
from django.views import generic
from . import views

nic_patterns = patterns(
    'configure.views',

    url(r'^network/interfaces$', 'nic_list', name='network-interface-list'),
    url(r'(?P<slug>(eth|ib)\d)$', 'nic_config', name='network-interface-update'),

    #(r'^detail/(?P<interface>(eth|ib)\d+)$', NetworkInterfaceDetailView.as_view()),
    #url(r'add$', NetworkInterfaceConfigCreate.as_view(), name='network-interface-add'),
    #url(r'config/(?P<slug>(eth|ib)\d+)$', NetworkInterfaceConfigUpdate.as_view(), name='network-interface-config-update'),
    #url(r'config/(?P<slug>(eth|ib)\d+)/delete$', NetworkInterfaceConfigDelete.as_view(), name='network-interface-config-delete'),
)

urlpatterns = patterns(
    'configure.views',
    url(r'^$', 'home', name='configure'),

    #(r'^network$', NetworkDetailView.as_view()),
    url(r'^network/$', include(nic_patterns)),
)

