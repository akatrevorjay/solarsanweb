from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from storage.models import Pool, Dataset, Filesystem, Snapshot

class HomeListView( generic.TemplateView ):
    template_name = 'configure/home_list.html'
    def get( self, request, *args, **kwargs ):
        context = {}
        return self.render_to_response( context )

"""
Cluster
"""
from django.core.cache import cache
import gluster

class ClusterPeerListView( generic.TemplateView ):
    template_name = 'configure/cluster/peer_list.html'
    def get( self, request, *args, **kwargs ):
        peers = gluster.peer.status()
        discovered_peers = cache.get( 'RecentlyDiscoveredClusterNodes' )
        discovered_peers.pop( '127.0.0.1' )  # Remove localhost

        context = {
                'peers': peers['host'],
                'discovered_peers': discovered_peers,
                'peer_count': peers['peers'],
                }
        return self.render_to_response( context )

class ClusterPeerDetailView( generic.TemplateView ):
    template_name = 'configure/cluster/peer_detail.html'
    def get( self, request, *args, **kwargs ):
        peers = gluster.peer.status()

        peer_host = kwargs.get( 'peer' )
        if not peer_host in peers['host'].keys(): raise http.Http404

        peer = {peer_host: peers['host'][peer_host]}

        context = {
                'peers': peers['host'],
                'peer': peer,
                'peer_count': peers['peers'],
               }
        return self.render_to_response( context )

"""
Network
"""
import netifaces

class NetworkDetailView( generic.TemplateView ):
    template_name = 'configure/network/network_detail.html'
    def get( self, request, *args, **kwargs ):
        context = {}
        return self.render_to_response( context )

def get_ifaces( *args ):
    """ Helper to get a list of interfaces and it's properties """
    interfaces = {}
    af_types = netifaces.address_families

    if args: get_ifaces = args
    else:    get_ifaces = netifaces.interfaces()

    for iface in get_ifaces:
        iftype = None
        if   iface.startswith('eth'):   iftype = 'ethernet'
        elif iface.startswith('ib'):    iftype = 'infiniband'

        interfaces[iface] = {'name': iface,
                             'addrs': dict( map( lambda x: ( af_types[ x[0] ], x[1] ), netifaces.ifaddresses( iface ).items() ) ),
                             ## TODO Grab DNS
                             'dns': {'nameservers': ['8.8.8.8', '8.8.4.4'],
                                     'search': 'solarsan.local',
                                     },
                             'type': iftype,
                             ## TODO Get real network IP info from DB
                             'config': {'proto': 'static',
                                        'ipaddr': '10.0.0.1',
                                        'netmask': '255.255.255.0',
                                        'gateway': '10.0.0.254',
                                        'dns': {'servers': ['8.8.8.8', '8.8.4.4'],
                                                'search': ['solarsan.local'],
                                                },
                                        },
                             }
    return interfaces

class NetworkInterfaceListView( generic.TemplateView ):
    template_name = 'configure/network/interface_list.html'
    def get( self, request, *args, **kwargs ):
        interfaces = get_ifaces()
        del interfaces['lo']    # Don't show lo interface
        context = {'interfaces': interfaces, }
        return self.render_to_response( context )

class NetworkInterfaceDetailView( generic.TemplateView ):
    template_name = 'configure/network/interface_detail.html'
    def get( self, request, *args, **kwargs ):
        interfaces = get_ifaces()
        del interfaces['lo']    # Don't show lo interface
        context = {'interface': kwargs['interface'],
                   #'interfaces': get_ifaces( kwargs['interface'] ),
                   'interfaces': interfaces,
                   }
        return self.render_to_response( context )



