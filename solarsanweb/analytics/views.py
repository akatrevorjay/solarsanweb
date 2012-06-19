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

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

import json

from django.conf import settings
import pyflot
import os, sys

from django.shortcuts import render_to_response
from django.template import RequestContext

def home(request, *args, **kwargs):
    return render_to_response('analytics/home.html',
        {'title': 'Analytics',
            },
        context_instance=RequestContext(request))

def render(request, *args, **kwargs):
    # TODO get programmatically
    #pool = Pool.objects.all()[0]
    #logger.error('args=%s kwargs=%s post=%s', args, kwargs, request.GET)

    values = {}

    #if not request.GET['name'] in ['iops_read', 'iops_write', 'bandwidth_read', 'bandwidth_write']:
    #    raise http.Http404

    #count = 50
    #iostats = pool.pool_iostat_set.order_by('timestamp')[:count]

    ##total = int(iostats[0].alloc + iostats[0].free)
    ##graph['usage'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

    #values['iops'] = {'read': [], 'write': []}
    #values['bandwidth'] = {'read': [], 'write': []}

    #for iostat in iostats:
    #    time = int(iostat.timestamp.strftime('%s')) * 1000

    #    values['iops']['read'].append( (time, int(iostat.iops_read) ) )
    #    values['iops']['write'].append( (time, int(iostat.iops_write) ) )
    #    values['bandwidth']['read'].append( (time, int(iostat.bandwidth_read) ) )
    #    values['bandwidth']['write'].append( (time, int(iostat.bandwidth_write) ) )

    for rrd_file in [request.GET['name']]:
        rrd_path=os.path.join(settings.DATA_DIR, 'rrd', rrd_file + '.rrd')
        rrd = RRD(rrd_path, mode="r")
        rrd_data = rrd.fetch(resolution=int(request.GET['step']), cf='AVERAGE',
                  start=int(request.GET['start']),
                  end=int(request.GET['stop']),
                  returnStyle='ds')

        values[rrd_file] = []

        def fix_nan(x):
            x = list(x)
            if x[1] != x[1]: x[1] = 0
            return [x[0] * 1000, x[1]]

        for ds in rrd_data.iterkeys():
            values[rrd_file].append( { 'key': ds, 'values': map(fix_nan, rrd_data[ds]) } )

    return http.HttpResponse(json.dumps(values), mimetype="application/json")


#@cache_page(15)
def graphs(request, *args, **kwargs):
    pool = Pool.objects.all()[0]
    graphs = {}

    for iostat_graph in ['bandwidth', 'iops']: #usage
        graphs[iostat_graph] = pyflot.Flot()

    count = 50
    iostats = pool.pool_iostat_set.order_by('timestamp')[:count]

    #total = int(iostats[0].alloc + iostats[0].free)
    #graph['usage'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

    iops = {'read': [], 'write': []}
    bandwidth = {'read': [], 'write': []}

    for iostat in iostats:
        time = int(iostat.timestamp.strftime('%s')) * 1000

        iops['read'].append( (time, int(iostat.iops_read) ) )
        iops['write'].append( (time, int(iostat.iops_write) ) )
        bandwidth['read'].append( (time, int(iostat.bandwidth_read) ) )
        bandwidth['write'].append( (time, int(iostat.bandwidth_write) ) )

    graphs['iops'].add_series(iops['read'], label='IOPs Read', )
    graphs['iops'].add_series(iops['write'], label='IOPs Write', )

    graphs['bandwidth'].add_series(bandwidth['read'], label='BW Read', )
    graphs['bandwidth'].add_series(bandwidth['write'], label='BW Write', )

    for iostat_graph in ['bandwidth', 'iops']: #usage
        graphs[iostat_graph]._options = {
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

    return render_to_response('analytics/graphs.html',
            {'graphs': graphs,
                }, context_instance=RequestContext(request))


