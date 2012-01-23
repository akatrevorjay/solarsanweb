from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

from utils import qdct_as_kwargs
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

from solarsan.utils import convert_human_to_bytes, zpool_iostat, zpool_list, zfs_list
from solarsan.models import Pool, Pool_IOStat

def status(request):
    """ Displays status of SAN """

    datasets = zfs_list()
    #zpools = [i for i in zfs_datasets if len(zfs_datasets[i]['parent']) <= 0]
    zpools = zpool_list()
    
    return render_to_response('solarsan/status.html',
        {'title': 'Status',
         'datasets': datasets,
         'pools': zpools,
         'graph_stats': graph_stats(20)},
        context_instance=RequestContext(request))

def graph_stats(count=1):
    graph = {}

    for p in Pool.objects.all():
        #iostats = p.pool_iostat_set.order_by('timestamp')[:count:offset]
        iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
        
        graph[p.name] = {}

        total = int(iostats[0].alloc + iostats[0].free)
        graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

        graph[p.name]['graph_iops'] = {'values': []}
        graph[p.name]['graph_throughput'] = {'values': []}
        for iostat in iostats:
            graph[p.name]['graph_iops']['values'].append([int(iostat.iops_read), int(iostat.iops_write)])
            graph[p.name]['graph_throughput']['values'].append([int(iostat.bandwidth_read) / 1024 / 1024, int(iostat.bandwidth_write) / 1024 / 1024])

    return graph

def pool_utilization():
    graph = {}

    for p in Pool.objects.all():
        #iostats = p.pool_iostat_set.order_by('timestamp')[:count:offset]
        iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
        
        graph[p.name] = {}

        total = int(iostats[0].alloc + iostats[0].free)
        graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

    return graph
    


@csrf_exempt
def graph_stats_json(request):
    return JSONResponse(graph_stats(20))

