from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from solarsan.utils import *
from solarsan.models import *
from solarsan.forms import *

from datetime import datetime, timedelta
#import time
from pyrrd.rrd import RRD
from pyrrd.backend import bindings

from django.conf import settings
import zfs
import pyflot
import os, sys

class LoggedInMixin(object):
    """ A mixin requiring a user to be logged in. """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise http.Http404
        return super(LoggedInMixin, self).dispatch(request, *args, **kwargs)

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

def status(request, *args, **kwargs):

    pools = Pool.objects.all()

    pool = kwargs.get('pool', request.GET.get('pool'))
    # TODO 404 instead
    if not pool in pools: pool = pools[0]

    return render_to_response('status.html',
        {'title': 'Status',
         'pools': pools,
         'pool': pool,
            },
        context_instance=RequestContext(request))

@csrf_exempt
def status_pool(request, *args, **kwargs):
    """ Status: Gets pool """

    ## IMPORTANT TODO FUCK clean the dataset argument
    pool = kwargs.get('pool', request.GET.get('pool'))
    pool = Filesystem.objects.get(name=pool)

    return render_to_response('status/pool.html',
            {'pool': pool }, context_instance=RequestContext(request))


@csrf_exempt
def status_dataset(request, *args, **kwargs):
    """ Status: Gets dataset """

    ## IMPORTANT TODO FUCK clean the dataset argument
    dataset = kwargs.get('dataset', request.GET.get('dataset'))
    dataset = Filesystem.objects.get(name=dataset)

    return render_to_response('status/dataset.html',
            {'dataset': dataset }, context_instance=RequestContext(request))


@csrf_exempt
def status_dataset_action(request, *args, **kwargs):
    """ Status: Gets dataset action """

    ctxt = {}

    ## IMPORTANT TODO FUCK clean the action argument
    action = kwargs.get('action', request.GET.get('action', 'health'))
    dataset = kwargs.get('dataset', request.GET.get('dataset'))

    ctxt['dataset'] = Filesystem.objects.get(name=dataset)

    if action == "cron":
        ctxt['dataset_service_form'] = DatasetServiceForm()
        ctxt['dataset_cron_form'] = DatasetCronForm()
        #ctxt['dataset_autosnap_form'] = DatasetAutoSnapForm()
        #ctxt['dataset_online_backup_form'] = DatasetOnlineBackupForm()

        # TODO Either make a seperate scheduler page or filter these out
        #   Probably easiest to just make a scheduler page.
        ctxt['crons'] = Cron.objects.all()

    ctxt['action'] = action

    return render_to_response('status/dataset/'+action+'.html',
                              ctxt, context_instance=RequestContext(request))



@cache_page(15)
def graphs(request, *args, **kwargs):
    pools = Pool.objects.all()

    graphs = {}
    for rrd_file in ['cache_result', 'arc_hitmiss', 'cache_size', 'dmu_tx']:
        #graph.add_line([ (x,y), (x,y) ])
        rrd_path=os.path.join(settings.DATA_DIR, 'rrd', rrd_file + '.rrd')
        rrd = RRD(rrd_path, mode="r")

        endTime = datetime.now()
        startTime = endTime - timedelta(hours=5)

        graphs[rrd_file] = pyflot.Flot()
        rrd = RRD(rrd_path, mode="r")
        rrd_data = rrd.fetch(resolution=300 * 12, cf='AVERAGE',
                  start=startTime.strftime('%s'),
                  end=endTime.strftime('%s'),
                  returnStyle='ds')

        for ds in rrd_data.keys():
            d = []
            for (x,y) in rrd_data[ds]:
                try:
                    time = int(datetime.fromtimestamp(int(x)).strftime('%s')) * 1000
                    data = int(y)
                    if data > 1000:
                        data = data / 1000 / 1000
                except:
                    data = 0
                d.append( ( time, data ) )
            graphs[rrd_file].add_series(d, label=ds, )

        graphs[rrd_file]._options = {
            'xaxis': {  'mode': 'time',
                        #'position': 'top',
                        #'tickDecimals': 0, 'tickSize': 1,
                        'minTickSize': [1, "minute"],
                        'twelveHourClock': True,
                        'timeFormat': '%I:%m%p',
                        #'autoscaleMargin': 1,
                        #'reserveSpace': False,
                        #'localTimezone': True,
                        },
            'yaxis': {  #'autoscaleMargin': 1,
                        #'reserveSpace': False,
                        'labelWidth': 25,
                     },
            'lines': { 'show': True, },
            'points': { 'show': True, },
            'height': '200px',
            'grid': {
                'backgroundColor': { 'colors': ["#fff", "#eee"] },
                #'hoverable': True,
                #'autoHighlight': True,
                #'axisMargin': 0,
                #'labelMargin': 0,
                #'': ,
                },
            #'crosshair': { 'mode': "x" },
            'legend': {
                'show': True,
                #labelFormatter: null or (fn: string, series object -> string)
                #labelBoxBorderColor: color
                'noColumns': 2,
                'position': "ne",
                #position: "ne" or "nw" or "se" or "sw"
                #margin: number of pixels or [x margin, y margin]
                #'margin': 0,
                #backgroundColor: null or color
                #backgroundOpacity: number between 0 and 1
                'backgroundOpacity': 0.75,
                #container: null or jQuery object/DOM element/jQuery expression
                #'container': '#flotconttest',
            },
        }

    return render_to_response('graphs.html',
            {'graphs': graphs, 'pools': pools,
                }, context_instance=RequestContext(request))



def scheduler(request, *args, **kwargs):
    """ Scheduler: View/modify scheduled tasks """
    crons = Cron.objects.all()

    return render_to_response('scheduler.html',
            {'crons': crons,
                }, context_instance=RequestContext(request))


