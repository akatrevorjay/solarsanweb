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
        discovered_peers.pop( '127.0.0.1' )

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

class NetworkInterfaceListView( generic.TemplateView ):
    template_name = 'configure/network/interface_list.html'
    def get( self, request, *args, **kwargs ):
        ## FUCK This is a quick hack, and this data structure should IMO be more like what's in the interfaces generator template
        interfaces = dict( map( 
                               lambda x: ( x, dict( ( ( 'name', x ), ( 'addrs', netifaces.ifaddresses( x ) ) ) ) ),
                               netifaces.interfaces()
                               ) )

        ## FUCK Only show interfaces that match /^(eth|ib)\d+$/
        # Don't show lo interface
        del interfaces['lo']

        context = {'interfaces': interfaces, }
        return self.render_to_response( context )

class NetworkInterfaceDetailView( generic.TemplateView ):
    template_name = 'configure/network/interface_detail.html'
    def get( self, request, *args, **kwargs ):
        interface = {'name': kwargs['interface'],
                     'addrs': netifaces.ifaddresses( kwargs['interface'] ), }
        context = {'interface': interface, }
        return self.render_to_response( context )



