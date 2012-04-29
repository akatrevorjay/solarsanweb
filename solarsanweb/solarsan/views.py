from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core import serializers

from chartit import DataPool, Chart
from utils import qdct_as_kwargs
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

from solarsan.utils import *
from solarsan.models import *

def status(request):

    pools = Pool.objects.all()

    def convert_timestamp(dt):
        return dt.strftime('%H:%M%P')

   ## TODO ArcStats
    ds = DataPool(
           series=
            [{  'options':    { 'source': Pool_IOStat.objects.all()[:10],  },
                'terms':      [ 'iops_read', 'iops_write', 'bandwidth_read', 'bandwidth_write', 'timestamp', 'free', 'alloc', ], },
             #{  'options':    { 'source': Dataset.objects.filter(type='filesystem'), },
             #   'terms':      [ 'compressratio', 'used', 'usedbychildren', 'usedbyrefreservation', 'usedbydataset', 'usedbysnapshots', ],

             #}
            ]
    )

    graph_activity = Chart(
            datasource=ds,
            series_options=
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':{
                   'timestamp': [ 'bandwidth_read', 'bandwidth_write', 'iops_read', 'iops_write', ],
                   #'timestamp': [ 'used', 'usedbychildren', 'usedbyrefreservation', 'usedbydataset', 'usedbysnapshots', ],
                  }}],
            chart_options=
              { #'title': { 'text': 'Pool/Dataset Activity'},
               'xAxis': {
                    'title': {
                       'text': 'Timestamp'}}}, x_sortf_mapf_mts=(None, convert_timestamp, False))

#  s = DataPool(
           #series=
            #[{'options': {
                #'source': pools,
              #'terms': [
                #'name',
                #'capacity'
                #''
                #'']}
             #])

    #cht = Chart(
            #datasource=ds,
            #series_options=
              #[{'options':{
                  #'type': 'pie',
                  #'stacking': False},
                #'terms':{
                  #'month': [
                    #'boston_temp']
                  #}}],
            #chart_options=
              #{'title': {
                   #'text': 'Monthly Temperature of Boston'}},
            #x_sortf_mapf_mts=(None, monthname, False))
    ##end_code

    #Step 1: Create a DataPool with the data we want to retrieve.
    capacitydata = \
        DataPool(
           series=[
               {'options': {
                   'source': Pool_IOStat.objects.all()[:20]
                },
                   'terms': [ 'timestamp',
                        'alloc',
                        'free',
                  ]},
                ])

    #Step 2: Create the Chart object
    graph_capacity = Chart(
            datasource=capacitydata,
            series_options=
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':{
                  'timestamp': [
                    'alloc',
                    'free']
                  }}],
            chart_options=
              {'title': {
                   'text': 'Pool capacity over time'},
               'xAxis': {
                    'title': {
                       'text': 'Timestamp'}}}, x_sortf_mapf_mts=(None, convert_timestamp, False))

    return render_to_response('solarsan/status.html',
        {'title': 'Status',
         'pools': pools,
         'graph_capacity': graph_capacity,
         'graph_activity': graph_activity, },
        context_instance=RequestContext(request))

@csrf_exempt
def status_dataset_info(request, *args, **kwargs):
    """ Status: Gets dataset info """

    action = kwargs.get('action', request.GET.get('action'))
    dataset = kwargs.get('dataset', request.GET.get('dataset'))

    if action == "snapshots" or action == "health":
        d = Dataset.objects.get(name=dataset, type='filesystem')
    else:
        d = Dataset.objects.get(name=dataset)
    return render_to_response('solarsan/status_dataset_info.html',
                                  {'dataset': d,
                                   'action': action,
                                   }, context_instance=RequestContext(request))

@csrf_exempt
def graph_stats_json(request):
    return JSONResponse(graph_stats(10))

