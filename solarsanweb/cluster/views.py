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
from .models import ClusterNode

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
        #discovered_peers = cache.get('RecentlyDiscoveredClusterNodes')
        discovered_peers = ClusterNode.objects.all()
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
