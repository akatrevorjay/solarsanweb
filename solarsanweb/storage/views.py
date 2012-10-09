
from dj import generic, http, reverse, HttpResponse, render
import storage.forms as forms

#from datetime import timedelta
import mongogeneric
import logging
import json

from solarsan.views import JsonMixIn, KwargsMixIn
from storage.models import Pool, Dataset, Filesystem, Snapshot, Volume
from analytics.views import time_window_list


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. generic.edit.CreateView)
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



"""
Bases
"""


class CrumbMixin(object):
    def get_context_data(self, *args, **kwargs):
        ctx = super(CrumbMixin, self).get_context_data(*args, **kwargs)
        obj = ctx.get('object')
        if not obj:
            return ctx
        #path = getattr(self, 'breadcrumbs', None)
        path = None
        func = getattr(obj, 'path', None)
        if not func or isinstance(func, basestring):
            return ctx
        for p in func():
            if not path:
                path = p
            else:
                path += '/%s' % p
            obj_type = getattr(obj, 'type', None)
            if obj_type:
                url = reverse(obj_type, None, None, {'slug': path})
                self.request.breadcrumbs(p, url)
        return ctx


class BaseView(CrumbMixin, KwargsMixIn):
    pass


"""
Pools
"""


class PoolView(BaseView):
    document = Pool
    slug_field = 'name'
    context_object_name = 'pool'


class PoolHealthView(PoolView, mongogeneric.DetailView):
    template_name = 'storage/pool_health.html'
    pass

pool_health = PoolHealthView.as_view()


class PoolAnalyticsDetailView(PoolView, mongogeneric.DetailView):
    template_name = 'storage/pool_analytics.html'
    charts = ['iops', 'bandwidth', 'usage']
    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsDetailView, self).get_context_data(**kwargs)
        time_window = int( self.kwargs.get( 'time_window', 86400 ) );
        if not time_window in time_window_list:
            raise http.Http404
        name = self.kwargs.get( 'name', 'iops' )
        if not name in self.charts:
            raise http.Http404

        ctx.update({'title': 'Analytics',
                    'graph_list': self.charts,
                    'time_window': time_window,
                    'time_window_list': time_window_list,

                    'graph': name, })
        return ctx

pool_analytics = PoolAnalyticsDetailView.as_view()


class PoolAnalyticsRenderView(JsonMixIn, PoolAnalyticsDetailView):
    def get_json_data(self, **kwargs):
        ctx = self.get_context_data(**kwargs)
        obj = self.object
        render_func = getattr(obj.analytics, ctx['graph'])
        kwargs['start'] = self.request.GET.get('start')
        kwargs['format'] = 'nvd3'
        ret = render_func(**kwargs)
        return ret

pool_analytics_render = PoolAnalyticsRenderView.as_view()


"""
Datasets
"""

class DatasetView(BaseView):
    document = Dataset
    slug_field = 'name'
    context_object_name = 'dataset'
    def get_context_data(self, **kwargs):
        ctx = super(DatasetView, self).get_context_data(**kwargs)
        ctx['pool'] = ctx[self.context_object_name].pool
        return ctx


class DatasetCreateView(object):
    template_name = 'storage/dataset_create.html'


class DatasetDeleteView(object):
    template_name = 'storage/dataset_delete.html'


class DatasetHealthView(object):
    template_name = 'storage/dataset_health.html'


class DatasetSnapshotsView(object):
    template_name = 'storage/dataset_snapshots.html'


"""
Filesystem
"""


class FilesystemView(DatasetView):
    document = Filesystem


class FilesystemHealthView(FilesystemView, DatasetHealthView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_health.html'

filesystem_health = FilesystemHealthView.as_view()


class FilesystemSnapshotsView(FilesystemView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_snapshots.html'

filesystem_snapshots = FilesystemSnapshotsView.as_view()


"""
Volumes
"""


class VolumeView(DatasetView):
    document = Volume

    def get_context_data(self, **kwargs):
        context = super(VolumeView, self).get_context_data(**kwargs)
        return context


class VolumeHealthView(VolumeView, DatasetHealthView, mongogeneric.DetailView):
    template_name = 'storage/volume_health.html'

    def get_context_data(self, **kwargs):
        context = super(VolumeHealthView, self).get_context_data(**kwargs)
        #context['targets'] = storage.target.target_list(fabric_module=fabric)
        context['targets'] = storage.target.target_list(cached=True)
        #context['backstore'] = backstore = self.object.backstore()
        context['luns'] = list(context['object'].backstore().attached_luns)
        return context

volume_health = VolumeHealthView.as_view()


class VolumeSnapshotsView(VolumeView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/volume_snapshots.html'
    pass

volume_snapshots = VolumeSnapshotsView.as_view()


"""
Targets
"""

import storage.target
import storage.cache

fabric = storage.target.get_fabric_module('iscsi')

class TargetDetailView(BaseView, generic.DetailView):
    template_name = 'storage/target_detail.html'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = storage.target.get(wwn=slug)
        except storage.target.DoesNotExist:
            raise http.Http404
        return obj

target_detail = TargetDetailView.as_view()


class TargetCreateView(generic.edit.FormView):
    template_name = 'storage/target_create.html'
    form_class = forms.TargetCreateForm
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        logging.debug('form=%s', form)
        return super(TargetCreateView, self).form_valid(form)

target_create = TargetCreateView.as_view()


class TargetPortalGroupUpdateView(AjaxableResponseMixin, KwargsMixIn, generic.edit.FormView):
    template_name = 'storage/target_detail.html'
    form_class = forms.TargetPortalGroupUpdateForm
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        assert self.request.is_ajax()
        data = form.cleaned_data

        target_wwn = self.kwargs['slug']
        target = storage.target.get(target_wwn)

        tag = int(self.kwargs['tag'])
        tpg = target.get_tpg(tag)

        if not tpg:
            raise Exception("Could not find TPG with tag='%s' for Target with '%s'",  tag, target)

        logging.info("Updating TPG: '%s'", data)

        enable = int(data['enable'])
        if enable == 1:
            tpg.enable = 1
        else:
            tpg.enable = 0

        ret = {'enable': tpg.enable}
        return self.render_to_json_response(ret)

target_portal_group_update = TargetPortalGroupUpdateView.as_view()


def target_portal_group_update2(request, slug=None, tag=None):
    if request.method == 'POST':  # If the form has been submitted...
        status = None
        form = forms.TargetPortalGroupForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
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
        form = forms.TargetPortalGroupForm()   # An unbound form
        #form.target_wwn = target.wwn
        #form.tag = target_portal_group.tag

    context = {}

    context['form'] = form

    return render(request, 'storage/target_detail.html', context)



class ContactView(generic.FormView):
    template_name = 'contact.html'
    #form_class = ContactForm
    success_url = '/thanks/'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return super(ContactView, self).form_valid(form)

