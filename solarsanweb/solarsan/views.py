from django.template import RequestContext
#from django.utils.decorators import method_decorator
#from django.views.decorators.csrf import csrf_exempt
#from django.views.decorators.cache import cache_page, never_cache, patch_cache_control, patch_vary_headers, cache_control
#from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django import http
from django.views import generic

#from solarsan.utils import LoggedInMixIn
from storage.models import Pool, Dataset, Filesystem, Snapshot
from django.contrib.auth import authenticate, login
import mongogeneric
import json

"""
Base
"""

def base_site_js(request):
    """ Returns base.js, rendered with site wide js includes """
    ctxt = {}
    return render_to_response('base_site.js',
                              ctxt, context_instance=RequestContext(request))



"""
Auth
"""

def login_view(request):
    """ Authenticates user """
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            # Redirect to a success page.
        else:
            # Return a 'disabled account' error message
            pass
    else:
        # Return an 'invalid login' error message.
        pass

"""
MixIns
The kool-aid.
"""

class KwargsMixIn(object):
    """ Adds request and kwargs to object """
    def get(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return super(KwargsMixIn, self).get(request, *args, **kwargs)


class JsonMixIn(object):
    """ Outputs self.get_json_data() as json"""
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        ret = self.get_json_data(*args, **kwargs)
        return http.HttpResponse(json.dumps(ret),
                                  mimetype="application/json", )

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = self.get_object()
        ret = self.post_json_data(*args, **kwargs)
        return http.HttpResponse(json.dumps(ret),
                                  mimetype="application/json", )



class LoggedInMixin( object ):
    """ A mixin requiring a user to be logged in. """
    def dispatch( self, request, *args, **kwargs ):
        if not request.user.is_authenticated():
            raise http.Http404
        return super( LoggedInMixin, self ).dispatch( request, *args, **kwargs )

"""
Generics
"""

class SingleDocumentMixIn(mongogeneric.SingleDocumentMixin):
    #zfs_obj = None

    #def get_context_data(self, **kwargs):
    #    ctx = super(SingleDocumentMixIn, self).get_context_data(**kw
    #    ctx_obj_name = self.context_object_name
    #    ctx['zfs_'+ctx_obj_name] = self.zfs_obj(ctx[ctx_obj_name])
    #    return ctx

    #def get_queryset(self):
    #    """
    #    Get the queryset to look an object up against. May not be calle
    #    `get_object` is overridden.
    #    """
    #    if self.queryset is None:
    #        if self.zfs_obj:
    #            return self.zfs_obj.dbm.objects()
    #        else:
    #            return super(SingleDocumentMixIn, self).get_queryset
    #    return self.queryset.clone()
    pass


class BaseDetailView(mongogeneric.BaseDetailView, SingleDocumentMixIn, mongogeneric.View):
    pass


class DetailView(mongogeneric.SingleDocumentTemplateResponseMixin, BaseDetailView):
    """
    Render a "detail" view of an object.

    By default this is a document instance looked up from `self.queryset
    view will support display of *any* object by overriding `self.get_ob
    """



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


