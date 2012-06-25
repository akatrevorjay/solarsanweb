from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page, never_cache, patch_cache_control, patch_vary_headers, cache_control
from django.views.decorators.vary import vary_on_cookie, vary_on_headers

### memcached keys must be < 120 bytes/chars, this silences the warning
#import warnings
#from django.core.cache import CacheKeyWarning
#warnings.simplefilter("ignore", CacheKeyWarning)

from django import http
from django.views import generic

from solarsan.utils import *
from storage.models import Pool, Dataset, Filesystem, Snapshot
#from solarsan.forms import *

#class AboutView(LoggedInMixin, generic.TemplateView):
#    """ About page view. """
#    template_name = 'about.html'
#
#    def get_context_data(self, **kwargs):
#        ctx = super(AboutView, self).get_context_data(**kwargs)
#        ctx['something_else'] = None  # add something to ctx
#        return ctx


#class SomeFormView(TemplateResponseMixin, View):
#    template_name = ''
#
#    def get(self, request):
#        form = SomeForm()
#
#        return self.render_to_response({
#            'form': form,
#        })
#
#    def post(self, request):
#        form = SomeForm(request.POST)
#
#        if form.is_valid():
#            form.save()
#            messages.success(request, 'Your form has been saved!')
#
#        return self.render_to_response({
#            'form': form,
#        })
#
#class AjaxThingView(View): 
#    # Note that I don't subclass the TemplateResponseMixin here!
#
#    def get(self, request):
#        return HttpResponse(status=404)
#
#    def post(self, request):
#        id = request.POST.get('id')
#
#        # Do something with the id
#        return HttpResponse('some data')


#class PoolView(object):
#    model = Pool

#class PoolListView(PoolView, generic.ListView):
#    pass

#class PoolDetailView(PoolView, generic.DetailView):
#    slug_field = Pool.name


#@csrf_exempt
#def status_dataset_action(request, *args, **kwargs):
#    """ Status: Gets dataset action """
#
#    ctxt = {}
#
#    ## IMPORTANT TODO FUCK clean the action argument
#    action = kwargs.get('action', request.GET.get('action', 'health'))
#    dataset = kwargs.get('dataset', request.GET.get('dataset'))
#
#    ctxt['dataset'] = Filesystem.objects.get(name=dataset)
#
#    if action == "cron":
#        ctxt['dataset_service_form'] = DatasetServiceForm()
#        ctxt['dataset_cron_form'] = DatasetCronForm()
#        #ctxt['dataset_autosnap_form'] = DatasetAutoSnapForm()
#        #ctxt['dataset_online_backup_form'] = DatasetOnlineBackupForm()
#
#        # TODO Either make a seperate scheduler page or filter these out
#        #   Probably easiest to just make a scheduler page.
#        ctxt['crons'] = Cron.objects.all()
#
#    ctxt['action'] = action
#
#    return render_to_response('status/dataset/'+action+'.html',
#                              ctxt, context_instance=RequestContext(request))


#def scheduler(request, *args, **kwargs):
#    """ Scheduler: View/modify scheduled tasks """
#    crons = Cron.objects.all()
#
#    return render_to_response('scheduler.html',
#            {'crons': crons,
#                }, context_instance=RequestContext(request))


