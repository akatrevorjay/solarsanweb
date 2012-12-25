
#from datetime import timedelta
import mongogeneric
import logging
#import json

from dj import generic, http, reverse, render, SessionWizardView
#from dj import HttpReponse
from django.conf import settings

from solarsan.utils import convert_human_to_bytes, convert_bytes_to_human, LoggedException, FormattedException
from solarsan.views import JsonMixin, KwargsMixin, AjaxableResponseMixin
from storage.models import Pool, Dataset, Filesystem, Snapshot, Volume
from analytics.views import time_window_list

import storage.forms as forms
import storage.target
import storage.cache
import rtslib


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


class BaseView(CrumbMixin, KwargsMixin):
    def get_context_data(self, **kwargs):
        ctx = super(BaseView, self).get_context_data(**kwargs)
        ctx['object_types_forms'] = get_object_forms()
        # TODO Remove this cache carp
        object_types_objects = storage.cache.storage_objects()
        ctx['object_types_objects'] = {}
        for k, vs in object_types_objects.iteritems():
            if k.endswith('s'):
                k = k[:-1]
            ctx['object_types_objects'][k] = vs
        return ctx


OBJECT_FORMS = {}


def get_object_forms():
    if 'pool' not in OBJECT_FORMS:
        OBJECT_FORMS.update({
            #'pool': {
            #    'create': forms.PoolCreateInitialForm(),
            #    #'remove': forms.PoolRemoveForm(),
            #},
            'filesystem': {
                'create': forms.FilesystemCreateForm(),
                #'remove': forms.FilesystemRemoveForm(),
            },
            'volume': {
                'create': forms.VolumeCreateForm(),
                #'remove': forms.VolumeRemoveForm(),
            },
            'target': {
                'create': forms.TargetCreateForm(),
                #'remove': forms.TargetRemoveForm(),
            },
        })
    return OBJECT_FORMS


"""
Pools
"""


class PoolView(BaseView):
    document = Pool
    slug_field = 'name'
    context_object_name = 'pool'

    #def get_context_data(self, **kwargs):
    #    ctx = super(PoolView, self).get_context_data(**kwargs)
    #    return ctx


class PoolDetailView(PoolView, mongogeneric.DetailView):
    template_name = 'storage/pool_health.html'
    pass

pool_health = PoolDetailView.as_view()


class PoolAnalyticsView(PoolView, mongogeneric.DetailView):
    template_name = 'storage/pool_analytics.html'
    charts = ['iops', 'bandwidth', 'usage']

    def get_context_data(self, **kwargs):
        ctx = super(PoolAnalyticsView, self).get_context_data(**kwargs)
        time_window = int(self.kwargs.get('time_window', 86400))
        if not time_window in time_window_list:
            raise http.Http404
        name = self.kwargs.get('name', 'iops')
        if not name in self.charts:
            raise http.Http404

        ctx.update({'title': 'Analytics',
                    'graph_list': self.charts,
                    'time_window': time_window,
                    'time_window_list': time_window_list,

                    'graph': name, })
        return ctx

pool_analytics = PoolAnalyticsView.as_view()


class PoolAnalyticsRenderView(JsonMixin, PoolAnalyticsView):
    def get_json_data(self, **kwargs):
        ctx = self.get_context_data(**kwargs)
        obj = self.object
        render_func = getattr(obj.analytics, ctx['graph'])
        kwargs['start'] = self.request.GET.get('start')
        kwargs['format'] = 'nvd3'
        ret = render_func(**kwargs)
        return ret

pool_analytics_render = PoolAnalyticsRenderView.as_view()


class PoolCreateView(PoolView, mongogeneric.CreateView):
    template_name = 'storage/pool_create.html'

#pool_create = PoolCreateView.as_view()


class PoolRemoveView(PoolView, mongogeneric.DeleteView):
    template_name = 'storage/pool_remove.html'

pool_remove = PoolRemoveView.as_view()


class PoolCreateWizardView(SessionWizardView):
    template_name = 'storage/pool_create_wizard.html'

    #def done(self, form_list, **kwargs):
    #    #do_something_with_the_form_data(form_list)
    #
    #    #return render_to_response('done.html', {
    #    #    'form_data': [form.cleaned_data for form in form_list],
    #    #})
    #
    #    #redirect_url = reverse(obj)
    #    redirect_url = reverse('home')
    #    return http.HttpResponseRedirect(redirect_url)

pool_create_wizard = PoolCreateWizardView.as_view([forms.PoolCreateInitialForm,
                                                   forms.DeviceFormSet])


"""
Datasets
"""


class DatasetView(BaseView):
    document = Dataset
    slug_field = 'name'
    context_object_name = 'dataset'

    def get_context_data(self, **kwargs):
        ctx = super(DatasetView, self).get_context_data(**kwargs)
        if 'object' in ctx:
            ctx['pool'] = ctx['object'].pool
        return ctx


class DatasetCreateView(object):
    template_name = 'storage/dataset_create.html'


class DatasetDeleteView(object):
    template_name = 'storage/dataset_delete.html'


class DatasetDetailView(object):
    template_name = 'storage/dataset_health.html'


class DatasetSnapshotsView(object):
    template_name = 'storage/dataset_snapshots.html'


"""
Filesystem
"""


class FilesystemView(DatasetView):
    document = Filesystem


class FilesystemDetailView(FilesystemView, DatasetDetailView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_health.html'

filesystem_health = FilesystemDetailView.as_view()


class FilesystemSnapshotsView(FilesystemView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/filesystem_snapshots.html'

filesystem_snapshots = FilesystemSnapshotsView.as_view()


class FilesystemCreateView(FilesystemView, DatasetCreateView, mongogeneric.CreateView):
    template_name = 'storage/filesystem_create.html'

filesystem_create = FilesystemCreateView.as_view()


class FilesystemRemoveView(FilesystemView, DatasetDeleteView, mongogeneric.DeleteView):
    template_name = 'storage/filesystem_remove.html'

filesystem_remove = FilesystemRemoveView.as_view()


"""
Volumes
"""


class VolumeView(DatasetView):
    document = Volume

    def get_context_data(self, **kwargs):
        context = super(VolumeView, self).get_context_data(**kwargs)
        return context


class VolumeDetailView(VolumeView, DatasetDetailView, mongogeneric.DetailView):
    template_name = 'storage/volume_health.html'

    def get_context_data(self, **kwargs):
        context = super(VolumeDetailView, self).get_context_data(**kwargs)
        #context['targets'] = storage.target.target_list(fabric_module=fabric)
        context['targets'] = storage.target.target_list()
        #context['backstore'] = backstore = self.object.backstore
        context['backstore'] = context['object'].backstore
        if context['backstore']:
            context['luns'] = list(context['backstore'].attached_luns)
        else:
            # Flash a warning through django's session flash
            pass

        return context

volume_health = VolumeDetailView.as_view()


class VolumeSnapshotsView(VolumeView, DatasetSnapshotsView, mongogeneric.DetailView):
    template_name = 'storage/volume_snapshots.html'
    pass

volume_snapshots = VolumeSnapshotsView.as_view()

import storage.dataset


class VolumeCreateView(VolumeView, DatasetCreateView, generic.edit.FormView):
    template_name = 'storage/filesystem_create.html'
    form_class = forms.VolumeCreateForm

    def form_valid(self, form):
        parent = form.cleaned_data.get('parent')
        basename = form.cleaned_data.get('name')
        name = '%s/%s' % (parent, basename)

        # Make sure size is given in correct and safe format
        size = form.cleaned_data.get('size')
        size = int(convert_human_to_bytes(size))
        size = convert_bytes_to_human(size)

        parent = Filesystem.objects.get(name=parent)
        pool = parent.pool

        logging.info("Creating Volume '%s' with parent='%s'", name, parent)

        obj = Volume()
        obj.pool = pool
        obj.name = name
        obj.create(size)
        obj.save()

        self.success_url = obj.get_absolute_url()
        return super(VolumeCreateView, self).form_valid(form)

volume_create = VolumeCreateView.as_view()


class VolumeRemoveView(VolumeView, DatasetDeleteView, mongogeneric.DeleteView):
    template_name = 'storage/filesystem_remove.html'

volume_remove = VolumeRemoveView.as_view()


"""
Target
"""


class TargetCreateView(KwargsMixin, generic.edit.FormView):
    template_name = 'storage/target_create.html'
    form_class = forms.TargetCreateForm

    def form_valid(self, form):
        fabric_name = form.cleaned_data['fabric_module']
        wwn = form.cleaned_data.get('target_wwn')

        logging.info("Creating Target with fabric='%s' wwn='%s'", fabric_name, wwn)
        obj = storage.target.create_target(fabric_name, wwn)

        self.success_url = reverse('target', kwargs={'slug': obj.wwn})
        return super(TargetCreateView, self).form_valid(form)

target_create = TargetCreateView.as_view()


class TargetDeleteView(KwargsMixin, generic.edit.FormView):
    template_name = 'storage/target_delete.html'
    form_class = forms.TargetDeleteForm

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = storage.target.get(wwn=slug)
        except storage.target.DoesNotExist:
            raise http.Http404
        return obj

    def get_form(self, form_class):
        self.object = self.get_object()
        form = form_class(**self.get_form_kwargs())
        form.helper.form_action = reverse('target-delete', kwargs={'slug': self.object.wwn})
        return form

    def form_valid(self, form):
        wwn = self.kwargs['slug']
        logging.info("Deleting Target with wwn='%s'", wwn)

        try:
            obj = storage.target.get(wwn)
            obj.delete()
            # TODO This would probably be better as either part of a wrapper
            # func (including deletion) in storage.target, or by altering
            # Target's method to do this itself.
            #storage.cache.cache.delete('targets')
        except storage.target.DoesNotExist:
            raise http.Http404

        #self.success_url = reverse('target-list')
        self.success_url = reverse('status')
        return super(TargetDeleteView, self).form_valid(form)

target_delete = TargetDeleteView.as_view()


class TargetDetailView(BaseView, generic.DetailView):
    template_name = 'storage/target_detail.html'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = storage.target.get(wwn=slug)
        except storage.target.DoesNotExist:
            raise http.Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super(TargetDetailView, self).get_context_data(**kwargs)
        obj = self.object

        context.update({
            'fabric_module': obj.fabric_module,
            'tpgs': list(obj.tpgs),
        })

        if settings.DEBUG:
            root = storage.target.root
            context.update(dict(
                rtslib_config_dump=root.dump(),
                rtslib_targets=list(root.targets),
                rtslib_tpgs=list(root.tpgs),
                rtslib_luns=list(root.luns),
                rtslib_node_acls=list(root.node_acls),
                network_portals=list(root.network_portals),
                rtslib_sessions=list(root.sessions),
                rtslib_fabric_modules=list(root.fabric_modules),
                rtslib_path=root.path,
                rtslib_storage_objects=list(root.storage_objects),
            ))

        return context

target_detail = TargetDetailView.as_view()


"""
Target Portal Group
"""


class TpgCreateView(KwargsMixin, generic.edit.CreateView):
    template_name = 'storage/target_pg_create.html'
    form_class = forms.TpgCreateForm

    def get_success_url(self):
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(TpgCreateView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        self.target = storage.target.get(wwn)
        return self.target

    def form_valid(self, form):
        self.get_object()
        logging.info('Creating TPG target=%s', self.target)
        tpg = rtslib.TPG(self.target, mode='create')
        tpg.enable = 1
        logging.debug("Created TPG '%s'", tpg)
        return super(TpgCreateView, self).form_valid(form)

target_pg_create = TpgCreateView.as_view()


class TpgUpdateView(AjaxableResponseMixin, KwargsMixin, generic.edit.BaseFormView):
    form_class = forms.AjaxTpgUpdateForm

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.tpg = storage.target.get_tpg(wwn, tag)
        return self.tpg

    def form_valid(self, form):
        data = form.cleaned_data
        tpg = self.get_object()

        if 'enable' in data:
            enable = bool(int(data['enable']))
            logging.info("Toggling TPG '%s' enable=%s", tpg, enable)
            tpg.enable = int(enable)
            return self.render_to_json_response(dict(
                enable=tpg.enable))

    #def render_to_response(self, ctx, **kwargs):
    #    return self.render_to_json_response(ctx, **kwargs)

target_pg_update = TpgUpdateView.as_view()


class TpgDeleteView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.ConfirmForm

    def get_success_url(self):
        # TODO Make this actually go somewhere that hasn't been deleted.
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(TpgDeleteView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.object = storage.target.get_tpg(wwn, tag)
        return self.object

    def form_valid(self, form):
        data = form.cleaned_data
        if data['confirm'] is not True:
            raise LoggedException("Did not confirm!")
        tpg = self.get_object()
        tpg.delete()
        return super(TpgDeleteView, self).form_valid(form)

target_pg_delete = TpgDeleteView.as_view()


"""
Target Portal Group Lun
"""


class LunCreateView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.LunCreateForm

    def get_success_url(self):
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(LunCreateView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.tpg = storage.target.get_tpg(wwn, tag)
        return self.tpg

    def form_valid(self, form):
        data = form.cleaned_data
        volume = Volume.objects.get(pk=data['volume'])
        tpg = self.get_object()
        tpg.lun(data['lun'], storage_object=volume.backstore)
        return super(LunCreateView, self).form_valid(form)

lun_create = LunCreateView.as_view()


class LunDeleteView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.ConfirmForm

    def get_success_url(self):
        # TODO Make this actually go somewhere that hasn't been deleted.
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(LunDeleteView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.object = storage.target.get_tpg(wwn, tag)
        return self.object

    def form_valid(self, form):
        data = form.cleaned_data
        if data['confirm'] is not True:
            raise LoggedException("Did not confirm!")
        tpg = self.get_object()
        lun_int = int(self.kwargs['lun'])
        the_lun = None
        for lun in tpg.luns:
            if lun.lun == lun_int:
                the_lun = lun
                break
        the_lun.delete()
        return super(LunDeleteView, self).form_valid(form)

lun_delete = LunDeleteView.as_view()


"""
Target Portal Group Network Portal
"""


class PortalCreateView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.PortalCreateForm

    def get_success_url(self):
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(PortalCreateView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.tpg = storage.target.get_tpg(wwn, tag)
        return self.tpg

    def form_valid(self, form):
        data = form.cleaned_data
        tpg = self.get_object()
        tpg.network_portal(data['ip'],
                           data['port'],
                           mode='create')
        return super(PortalCreateView, self).form_valid(form)

portal_create = PortalCreateView.as_view()


# TODO UNTESTED
class PortalDeleteView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.ConfirmForm

    def get_success_url(self):
        # TODO Make this actually go somewhere that hasn't been deleted.
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(PortalDeleteView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.object = storage.target.get_tpg(wwn, tag)
        return self.object

    def form_valid(self, form):
        data = form.cleaned_data
        if data['confirm'] is not True:
            raise LoggedException("Did not confirm!")
        ip_addr = data['ip_address']
        port = data['port']
        tpg = self.get_object()

        try:
            the_portal = None
            for portal in tpg.network_portals:
                if portal.ip_address == self.kwargs['ip_address'] and portal.port == self.kwargs['port']:
                    the_portal = portal
                    break
            if not the_portal:
                raise LoggedException("Could not find Portal to delete from Tpg '%s' with ip_address=%s port=%s", tpg, ip_address, port)
            the_portal.delete()
        except Exception, e:
            logging.error("Could not delete Portal with ip_address=%s port=%s: %s", ip_address, port, e)
            raise http.Http404

        return super(PortalDeleteView, self).form_valid(form)

portal_delete = PortalDeleteView.as_view()


"""
Target Portal Group Node ACL

"""

class AclCreateView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.AclCreateForm

    def get_success_url(self):
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(AclCreateView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.tpg = storage.target.get_tpg(wwn, tag)
        return self.tpg

    def form_valid(self, form):
        data = form.cleaned_data
        tpg = self.get_object()
        tpg.node_acl(data['node_wwn'],
                     mode='create')
        return super(AclCreateView, self).form_valid(form)

acl_create = AclCreateView.as_view()


# TODO UNTESTED
class AclDeleteView(KwargsMixin, generic.edit.UpdateView):
    template_name = 'modal_form.html'
    form_class = forms.ConfirmForm

    def get_success_url(self):
        # TODO Make this actually go somewhere that hasn't been deleted.
        return reverse('target', kwargs=dict(slug=self.kwargs['slug']))

    def get_form(self, form_class):
        # Set the correct form action URL
        form = super(AclDeleteView, self).get_form(form_class)
        form.helper.form_action = self.request.get_full_path()
        return form

    def get_object(self):
        wwn = self.kwargs['slug']
        tag = int(self.kwargs['tag'])
        self.object = storage.target.get_tpg(wwn, tag)
        return self.object

    def form_valid(self, form):
        data = form.cleaned_data
        if data['confirm'] is not True:
            raise LoggedException("Did not confirm!")
        tpg = self.get_object()
        the_acl = None
        for acl in tpg.network_acls:
            if acl.node_wwn == self.kwargs['node_wwn']:
                the_acl = acl
                break
        the_acl.delete()
        return super(AclDeleteView, self).form_valid(form)

acl_delete = AclDeleteView.as_view()


"""
Target Create Wizard
"""


class TargetCreateWizardView(SessionWizardView):
    template_name = 'storage/target_create_wizard.html'

    #def done(self, form_list, **kwargs):
    #    #do_something_with_the_form_data(form_list)
    #
    #    #return render_to_response('done.html', {
    #    #    'form_data': [form.cleaned_data for form in form_list],
    #    #})
    #
    #    #redirect_url = reverse(obj)
    #    redirect_url = reverse('home')
    #    return http.HttpResponseRedirect(redirect_url)

target_create_wizard = TargetCreateWizardView.as_view([forms.TargetCreateForm,
                                                       forms.TpgCreateForm,
                                                       forms.LunCreateForm,
                                                       forms.AclCreateForm,
                                                       ])


"""
Examples

def target_portal_group_update2(request, slug=None, tag=None):
    if request.method == 'POST':  # If the form has been submitted...
        status = None
        form = forms.TpgForm(request.POST)  # A form bound to the POST data
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
        form = forms.TpgForm()   # An unbound form
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
"""

''' Form Wizard Example
from django.http import HttpResponseRedirect
from django.contrib.formtools.wizard.views import SessionWizardView

FORMS = [("address", myapp.forms.AddressForm),
         ("paytype", myapp.forms.PaymentChoiceForm),
         ("cc", myapp.forms.CreditCardForm),
         ("confirmation", myapp.forms.OrderForm)]

TEMPLATES = {"address": "checkout/billingaddress.html",
             "paytype": "checkout/paymentmethod.html",
             "cc": "checkout/creditcard.html",
             "confirmation": "checkout/confirmation.html"}

def pay_by_credit_card(wizard):
    """Return true if user opts to pay by credit card"""
    # Get cleaned data from payment step
    cleaned_data = wizard.get_cleaned_data_for_step('paytype') or {'method': 'none'}
    # Return true if the user selected credit card
    return cleaned_data['method'] == 'cc'


class OrderWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        do_something_with_the_form_data(form_list)
        return HttpResponseRedirect('/page-to-redirect-to-when-done/')
'''
