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
import pyflot
import os, sys

from django.shortcuts import render_to_response
from django.template import RequestContext

def home(request, *args, **kwargs):
    return render_to_response('analytics.html',
        {'title': 'Analytics',
            },
        context_instance=RequestContext(request))


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


