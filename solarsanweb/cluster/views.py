import logging
import os
import sys

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic
import mongogeneric

from storage.models import Pool, Dataset, Filesystem, Volume, Snapshot
from solarsan.models import Config
from solarsan.views import KwargsMixin, AjaxableResponseMixin, JsonMixin
from django.core.cache import cache
import gluster
from .models import Node
from . import models
from . import serializers

#from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
from django.contrib import messages
from . import forms


"""
Cluster
"""


class HomeView(generic.TemplateView):
    template_name = 'cluster/home_list.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context)

home = HomeView.as_view()


class PeerListView(generic.TemplateView):
    template_name = 'cluster/peer_list.html'

    def get(self, request, *args, **kwargs):
        #peers = gluster.peer.status()
        #discovered_peers = cache.get('RecentlyDiscoveredNodes')
        discovered_peers = Node.objects.all()
        if discovered_peers:
            #discovered_peers = discovered_peers['nodes']
            #if '127.0.0.1' in discovered_peers:
                #discovered_peers.remove('127.0.0.1')  # Remove localhost
            pass

        context = {
            #'peers': peers['host'],
            'discovered_peers': discovered_peers,
            #'peer_count': peers['peers'],
        }
        return self.render_to_response(context)

peer_list = PeerListView.as_view()


class PeerDetailView(generic.TemplateView):
    template_name = 'cluster/peer_detail.html'

    def get(self, request, *args, **kwargs):
        #peers = gluster.peer.status()

        peer_host = kwargs.get('peer')
        if not peer_host in peers['host'].keys():
            raise http.Http404

        peer = {peer_host: peers['host'][peer_host]}

        context = {
            #'peers': peers['host'],
            #'peer': peer,
            #'peer_count': peers['peers'],
        }
        return self.render_to_response(context)

peer_detail = PeerDetailView.as_view()


"""
API
"""
from rest_framework import status
from rest_framework import renderers
from rest_framework import generics, mixins
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework import permissions

from configure.models import Nic
from django.conf import settings
from IPy import IP


class ClusterProbe(object):
    interfaces = None
    hostname = None


@api_view(['GET'])
def cluster_probe(request, format=None):
    """Cluster probe API"""
    if request.method == 'GET':
        ifaces = Nic.list()
        ret_ifaces = {}
        for iface_name, iface in ifaces.iteritems():
            for af, addrs in iface.addrs.iteritems():
                for addr in addrs:
                    if 'addr' not in addr or 'netmask' not in addr:
                        continue
                    if iface_name not in ret_ifaces:
                        ret_ifaces[iface_name] = {}
                    if af not in ret_ifaces[iface_name]:
                        ret_ifaces[iface_name][af] = []
                    ret_ifaces[iface_name][af].append((addr['addr'], addr['netmask']))
        ret = ClusterProbe()
        ret.hostname = settings.SERVER_NAME
        ret.interfaces = ret_ifaces
        #ret = {'hostname': settings.SERVER_NAME, 'interfaces': ret_ifaces}
        serializer = serializers.ClusterProbeSerializer(ret)
        return Response(serializer.data)


def get_node_by_ip(ip, nodes=None):
    if nodes is None:
        nodes = models.Node.objects.all()

    for node in nodes:
        for interface_name, interface in node.interfaces.items():
            for addrs_type_name, addrs in interface.items():
                for addr, netmask in addrs:
                    if ip == addr:
                        return node


class GenericObject(object):
    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __getitem__(self, k):
        return getattr(self, k)


@api_view(['GET'])
def cluster_ping(request, format=None):
    """Cluster ping"""
    source_ip = request.META['REMOTE_ADDR']
    source_node = get_node_by_ip(source_ip)
    logging.info("Cluster ping from source_node=%s, source_ip=%s", source_node, source_ip)

    if request.method == 'GET':
        ret = GenericObject()
        ret['pong'] = True
        serializer = serializers.ClusterPingSerializer(ret)
        return Response(serializer.data)


@api_view(['GET'])
def clustered_pool_heartbeat(request, format=None):
    """Clustered Pool Hearbeat"""
    source_ip = request.META['REMOTE_ADDR']
    source_node = get_node_by_ip(source_ip)
    #source_peer = models.Peer.objects.
    pool = storage.models.Pool.objects_clustered.get(name=request.GET['pool'])
    logging.info("Clustered Pool Heartbeat for pool=%s from source_node=%s, source_ip=%s",
                 pool, source_node, source_ip)

    if request.method == 'GET':
        #ret = ClusteredPoolHeartbeatObject()
        #
        #pools = ret.pools = {}
        #for pool in storage.models.Pool.objects_clustered.all():
        #    pools[pool.name] = {'is_healthy': pool.is_healthy(),
        #                        'cluster_state': pool.cluster_state,
        #                        }

        serializer = serializers.ClusteredPoolHeartbeatSerializer(pool)
        return Response(serializer.data)
