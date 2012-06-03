from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import TemplateView

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from solarsan.utils import *
from solarsan.models import *
from solarsan.forms import *

from datetime import datetime, timedelta
#import time
from pyrrd.rrd import RRD
from pyrrd.backend import bindings

from django.conf import settings
import pyflot
import os, sys

#class StatusView(TemplateView):
#        template_name = "status.html"

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

@cache_page(15)
def graphs(request, *args, **kwargs):
    pools = Pool.objects.all()

    graphs = {}
    for rrd_file in ['cache_result', 'arc_hitmiss', 'cache_size', 'cache_eviction']:
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



@csrf_exempt
def status_dataset_info(request, *args, **kwargs):
    """ Status: Gets dataset info """

    ctxt = {}

    action = kwargs.get('action', request.GET.get('action'))
    dataset = kwargs.get('dataset', request.GET.get('dataset'))

    if action == "snapshots" or action == "health":
        ctxt['dataset'] = Dataset.objects.get(name=dataset, type='filesystem')
    else:
        ctxt['dataset'] = Dataset.objects.get(name=dataset)

    if action == "cron":
        ctxt['dataset_service_form'] = DatasetServiceForm()
        ctxt['dataset_cron_form'] = DatasetCronForm()
        #ctxt['dataset_autosnap_form'] = DatasetAutoSnapForm()
        #ctxt['dataset_online_backup_form'] = DatasetOnlineBackupForm()

        # TODO Either make a seperate scheduler page or filter these out
        #   Probably easiest to just make a scheduler page.
        ctxt['crons'] = Cron.objects.all()

    ctxt['action'] = action

    return render_to_response('status_dataset_info.html',
                              ctxt, context_instance=RequestContext(request))


