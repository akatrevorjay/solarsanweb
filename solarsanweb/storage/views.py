#from django.shortcuts import render_to_response, get_object_or_404
#from django.template import RequestContext
#from django.contrib.auth.decorators import login_required
#from django.utils.decorators import method_decorator
#from django.views.decorators.csrf import csrf_exempt
#from django.views.decorators.cache import cache_page
#from django.core.cache import cache
from django import http
from django.views import generic

#from datetime import timedelta
import mongogeneric
import logging

from solarsan.views import JsonMixIn, KwargsMixIn
from storage.models import Pool, Dataset, Filesystem, Snapshot, Volume
from analytics.views import time_window_list

"""
Pools
"""

class PoolView(object):
    document = Pool
    slug_field = 'name'
    context_object_name = 'pool'


class PoolHealthDetailView(PoolView, KwargsMixIn, mongogeneric.DetailView):
    template_name = 'storage/pool_health.html'


class PoolAnalyticsDetailView(PoolView, KwargsMixIn, mongogeneric.DetailView):
    template_name = 'storage/pool_analytics.html'
    charts = ['iops', 'bandwidth', 'usage']
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        obj = self.object
        time_window = int( kwargs.get( 'time_window', 86400 ) );
        if not time_window in time_window_list:
            raise http.Http404
        name = kwargs.get( 'name', 'iops' )
        if not name in self.charts:
            raise http.Http404

        ctx.update({'title': 'Analytics',
                    'graph_list': self.charts,
                    'time_window': time_window,
                    'time_window_list': time_window_list,

                    'graph': name, })
        return ctx


class PoolAnalyticsRenderView(JsonMixIn, PoolAnalyticsDetailView):
    def get_json_data(self, **kwargs):
        ctx = self.get_context_data(**kwargs)
        obj = kwargs['object']
        render_func = getattr(obj.analytics, ctx['graph'])
        kwargs['start'] = kwargs['request'].GET.get('start')
        kwargs['format'] = 'nvd3'
        ret = render_func(**kwargs)
        return ret


"""
Datasets
"""

class DatasetView(object):
    document = Filesystem
    slug_field = 'name'
    context_object_name = 'dataset'
    def get_context_data(self, **kwargs):
        try:
            ctx = super(DatasetView, self).get_context_data(**kwargs)
        except:
            ctx = {}
        ctx['pool'] = ctx[self.context_object_name].pool
        return ctx

#class DatasetListView(DatasetView, mongogeneric.ListView):
#    context_object_name = 'datasets'
#    template_name = 'solarsan/dataset_list.html'

#class DatasetCreateView(DatasetView, mongogeneric.DetailView):
#    pass

#class DatasetDeleteView(DatasetView, mongogeneric.DetailView):
#    pass

class DatasetHealthDetailView(object):
    template_name = 'storage/dataset_health.html'
    pass

class DatasetSnapshotsView(object):
    template_name = 'storage/dataset_snapshots.html'
    pass


"""
Filesystem
"""


class FilesystemView(DatasetView):
    document = Filesystem
    context_object_name = 'filesystem'


class FilesystemHealthDetailView(FilesystemView, DatasetHealthDetailView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_health.html'
    pass


class FilesystemSnapshotsView(FilesystemView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_snapshots.html'
    pass


"""
Volumes
"""


class VolumeView(DatasetView):
    document = Volume


class VolumeHealthDetailView(VolumeView, DatasetHealthDetailView, mongogeneric.DetailView):
    template_name = 'storage/volume_health.html'

    def get_context_data(self, **kwargs):
        context = super(VolumeHealthDetailView, self).get_context_data(**kwargs)
        #context['targets'] = storage.target.target_list(fabric_module=fabric)
        targets = context['targets'] = storage.target.target_list(cached=True)
        return context


class VolumeSnapshotsView(VolumeView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/volume_snapshots.html'
    pass


"""
Targets
"""

import storage.target
import storage.cache

fabric = storage.target.get_fabric_module('iscsi')

a = mongogeneric.DetailView

class TargetDetailView(KwargsMixIn, generic.DetailView):
    template_name = 'storage/target_detail.html'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = storage.target.get(wwn=slug)
        except storage.target.DoesNotExist:
            raise http.Http404
        return obj


##
import json
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.views.generic.detail import SingleObjectTemplateResponseMixin

class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return super(AjaxableResponseMixin, self).form_invalid(form)

    def form_valid(self, form):
        if self.request.is_ajax():
            data = {
                'pk': form.instance.pk,
            }
            return self.render_to_json_response(data)
        else:
            return super(AjaxableResponseMixin, self).form_valid(form)
##


a = generic.edit.FormView

import storage.forms as forms

class TargetUpdateView(generic.edit.FormView):
    template_name = 'storage/target_detail.html'
    form_class = forms.TargetForm
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        logger.debug('form=%s', form)
        return super(ContactView, self).form_valid(form)


class TargetTPGUpdateView(AjaxableResponseMixin, generic.edit.FormView):
    template_name = 'storage/target_detail.html'
    form_class = forms.TargetTPGForm
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        assert self.request.is_ajax()
        form.save()
        ret = form.cleaned_data
        return self.render_to_json_response(ret)


from django.shortcuts import render
from django.http import HttpResponseRedirect

def tpg_update(request, slug=None, tag=None):
    if request.method == 'POST': # If the form has been submitted...
        status = None
        form = forms.TargetTPGForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            form.save()
            ret = form.cleaned_data
        else:
            status = 400
            ret = form.errors
        return http.HttpResponse(json.dumps(ret),
                                  mimetype="application/json",
                                  status=status)

    else:
        form = forms.TargetTPGForm() # An unbound form
        #form.target_wwn = target.wwn
        #form.tag = tpg.tag

    context = {}

    context['form'] = form

    return render(request, 'storage/target_detail.html', context)



class ContactView(generic.FormView):
    template_name = 'contact.html'
#    form_class = ContactForm
    success_url = '/thanks/'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return super(ContactView, self).form_valid(form)

