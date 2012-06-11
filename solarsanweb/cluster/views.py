from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from solarsan.models import Pool, Dataset, Filesystem, Snapshot
import gluster

class PeerListView(generic.TemplateView):
    template_name = 'cluster/peer_list.html'
    def get(self, request, *args, **kwargs):
        peers = gluster.peer.status()
        context = {
                'peers': peers['host'],
                'peer_count': peers['peers'],
                }
        return self.render_to_response(context)

class PeerDetailView(generic.TemplateView):
    template_name = 'cluster/peer_detail.html'
    def get(self, request, *args, **kwargs):
        peers = gluster.peer.status()

        peer_host = kwargs.get('peer')
        if not peer_host in peers['host'].keys():
            raise http.Http404

        peer = {peer_host: peers['host'][peer_host]}

        context = {
                'peers': peers['host'],
                'peer': peer,
                'peer_count': peers['peers'],
               }
        return self.render_to_response(context)



