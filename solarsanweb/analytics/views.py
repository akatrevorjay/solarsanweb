from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic
from django.utils import timezone
from django.conf import settings

from solarsan.utils import conditional_decorator
from storage.models import Pool, Dataset, Filesystem, Snapshot, PoolIOStat
#from solarsan.forms import *

from datetime import datetime, timedelta
#import time
from pyrrd.rrd import RRD
from pyrrd.backend import bindings

import logging
# Get an instance of a logger
logger = logging.getLogger( __name__ )

import json

from django.conf import settings
import pyflot
import os, sys

from django.shortcuts import render_to_response
from django.template import RequestContext

charts = ['iops', 'bandwidth', 'usage', # IOStats
          'arc_hitmiss', 'cache_eviction', 'cache_result', 'cache_size', 'dmu_tx_memory', 'dmu_tx', # RRD
          'hash_collisions', 'l2_hitmiss', 'mutex_operation']

time_window_list = {int( timedelta( hours=1 ).total_seconds() ):     'Last hour',
                    int( timedelta( hours=2 ).total_seconds() ):     'Last two hours',
                    int( timedelta( hours=12 ).total_seconds() ):    'Last twelve hours',
                    int( timedelta( days=1 ).total_seconds() ):      'Last day',
                    int( timedelta( days=7 ).total_seconds() ):      'Last week',
                    int( timedelta( days=30 ).total_seconds() ):     'Last month',
                    int( timedelta( days=365 ).total_seconds() ):    'Last year',
                    }

def home( request, *args, **kwargs ):
    time_window = int( kwargs.get( 'time_window', 86400 ) );
    if not time_window in time_window_list: raise http.Http404
    name = kwargs.get( 'name', 'iops' )
    if not name in charts: raise http.Http404
    return render_to_response( 'analytics/home.html',
        {'title': 'Analytics',
         'graph': name,
         'graph_list': charts,
         'time_window': time_window,
         'time_window_list': time_window_list,
            },
        context_instance=RequestContext( request ) )


from pypercube.cube import Cube
from pypercube.expression import EventExpression, MetricExpression, CompoundMetricExpression
from pypercube.expression import Sum, Min, Max, Median, Distinct
from pypercube import time_utils

def render_cube(request, *args, **kwargs):
    pool = 'rpool'
    pool = Pool.objects.get(name=pool)

    # Build the Cube connection configuration
    c = Cube('localhost')
    # Query for an Event and filter it
    e = EventExpression('pool_iostat', ['alloc', 'free',
                                        'bandwidth_read', 'bandwidth_write',
                                        'iops_read', 'iops_write'],
                        ).eq('pool', pool.name)
    #e = EventExpression("timing", ["path", "elapsed_ms"]).startswith('path', '/api/').eq('status', 200)
    # This is equivalent to the Cube query
    #   timing(path, elapsed_ms).re('path', '^/api/').eq('status', 200)
    # Set up some time boundaries
    stop = time_utils.now()
    start = time_utils.yesterday(stop)
    step = time_utils.STEP_1_HOUR
    # Fetch the matching events, returns Event objects
    #events = c.get_event(e, start=start, stop=stop, limit=10)
    #print events

    # Get the elapsed time of successful requests
    e_time = EventExpression("pool_iostat", "iops_write").eq('pool', pool.name)
    print e_time
    # Get the number of requests
    e_num = EventExpression("pool_iostat").eq('pool', pool.name)
    print e_num
    # Get a computed metric, returns Metric objects
    metrics = c.get_metric(Sum(e_time) / Sum(e_num), start=start, stop=stop, step=step)
    print metrics

    e_iops = EventExpression("pool_iostat", ['iops_read', 'iops_write']).eq("pool", pool.name)



#@conditional_decorator(not settings.DEBUG, cache_page, 15)
def render( request, *args, **kwargs ):
    """ Generates graph data in d3/nvd3 data format """
    name = request.GET['name']
    if name not in charts: raise http.Http404

    start = float( request.GET['start'] )
    stop = float( request.GET.get( 'stop', datetime.now().strftime('%s') ))
    step = float( request.GET['step'] )

    ret = []
    values = {}

    ## Pool_IOStat Graph
    if name in ['iops', 'bandwidth', 'usage']:
        if name == 'usage':
            fields = keys = ['alloc', 'free']
        elif name in ['iops', 'bandwidth']:
            keys = ['read', 'write']
            fields = ['%s_%s' % ( name, key ) for key in keys ]

        for key in keys:
            values[key] = []

        pool_name = 'rpool'
        pool = Pool.objects.get(name=pool_name)
        c = Cube('localhost')
        start = datetime.fromtimestamp(start)
        stop = datetime.fromtimestamp(stop)
        #stop = datetime.now(tz=timezone.utc)
        #step = long(step) * 60 * 1000
        step = time_utils.STEP_5_MIN

        for f in fields:
            e = EventExpression('pool_iostat', f).eq('pool', pool.name).gt(f, 0)
            metrics = c.get_metric(Median(e), start=start, stop=stop, step=step)
            values[f] = map(lambda x: (float(x.time.strftime('%s')) * 1000, x.value), metrics)

        ret = [ {'key': key.replace('_', ' ').title(),
                 'values': values[key] } for key in fields ]

    ## RRD Graph
    else:
        ## An RRD graph was requested
        rrd_path = os.path.join( settings.DATA_DIR, 'rrd', name + '.rrd' )
        rrd = RRD( rrd_path, mode="r" )
        rrd_data = rrd.fetch( resolution=int( step ), cf='AVERAGE',
                  start=start,
                  end=stop,
                  returnStyle='ds' )

        ret = [ { 'key': ds,
                  'values': map( lambda x: ( x[0] * 1000, x[1] ),
                                 filter( lambda x: x[1] == x[1], rrd_data[ds] )
                                 )
                 } for ds in rrd_data.keys() ]

    return http.HttpResponse( json.dumps( ret ), mimetype="application/json" )


#@cache_page( 15 )
def graphs( request, *args, **kwargs ):
    """ Generates graphs in Flot format """
    pool = Pool.objects.all()[0]        ## TODO Get this through request, this needs to not be hard coded!
    graphs = {}

    for iostat_graph in ['bandwidth', 'iops']: #usage
        graphs[iostat_graph] = pyflot.Flot()

    count = 50
    iostats = pool.pool_iostat_set.order_by( 'created' )[:count]

    #total = int(iostats[0].alloc + iostats[0].free)
    #graph['usage'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

    iops = {'read': [], 'write': []}
    bandwidth = {'read': [], 'write': []}

    for iostat in iostats:
        time = int( iostat.created.strftime( '%s' ) ) * 1000

        iops['read'].append( ( time, int( iostat.iops_read ) ) )
        iops['write'].append( ( time, int( iostat.iops_write ) ) )
        bandwidth['read'].append( ( time, int( iostat.bandwidth_read ) ) )
        bandwidth['write'].append( ( time, int( iostat.bandwidth_write ) ) )

    graphs['iops'].add_series( iops['read'], label='IOPs Read', )
    graphs['iops'].add_series( iops['write'], label='IOPs Write', )

    graphs['bandwidth'].add_series( bandwidth['read'], label='BW Read', )
    graphs['bandwidth'].add_series( bandwidth['write'], label='BW Write', )

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
        rrd_path = os.path.join( settings.DATA_DIR, 'rrd', rrd_file + '.rrd' )
        rrd = RRD( rrd_path, mode="r" )

        endTime = datetime.now()
        startTime = endTime - timedelta( hours=5 )

        graphs[rrd_file] = pyflot.Flot()
        rrd = RRD( rrd_path, mode="r" )
        rrd_data = rrd.fetch( resolution=300 * 12, cf='AVERAGE',
                  start=startTime.strftime( '%s' ),
                  end=endTime.strftime( '%s' ),
                  returnStyle='ds' )

        for ds in rrd_data.keys():
            d = []
            for ( x, y ) in rrd_data[ds]:
                try:
                    time = int( datetime.fromtimestamp( int( x ) ).strftime( '%s' ) ) * 1000
                    data = int( y )
                    if data > 1000:
                        data = data / 1000 / 1000
                except:
                    data = 0
                d.append( ( time, data ) )
            graphs[rrd_file].add_series( d, label=ds, )

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

    return render_to_response( 'analytics/graphs.html',
            {'graphs': graphs,
                }, context_instance=RequestContext( request ) )


