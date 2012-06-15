from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

#from solarsan.models import Pool, Dataset, Filesystem, Snapshot

class HomeListView(generic.TemplateView):
    template_name = 'configure/home_list.html'
    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context)

#class NetworkListView(generic.TemplateView):
#    template_name = 'configure/network_list.html'
#    def get(self, request, *args, **kwargs):
#        context = {}
#        return self.render_to_response(context)

class NetworkDetailView(generic.TemplateView):
    template_name = 'configure/network_detail.html'
    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context)



