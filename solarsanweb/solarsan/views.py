from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

from utils import qdct_as_kwargs
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

from solarsan.utils import convert_human_to_bytes, zpool_iostat, zfs_list

def status(request):
    """ Displays status of SAN """
    return render_to_response('solarsan/status.html',
        {'title': 'Status',
         'graph_stats': graph_stats(1)},
        context_instance=RequestContext(request))

def graph_stats(capture_length):
    if not capture_length:
        capture_length = 2

    iostats = zpool_iostat('rpool', capture_length)
    
    graph = {}

    used = int(convert_human_to_bytes(iostats[1])) / 1024 / 1024
    free = int(convert_human_to_bytes(iostats[2])) / 1024 / 1024
    total = int(used + free)
    graph['graph_utilization'] = {'values': [float(used / float(total) * 100), float(free / float(total) * 100)] }
    
    iops_read = int(iostats[3])
    iops_write = int(iostats[4])
    graph['graph_iops'] = {'values': [iops_read, iops_write]}
    
    read = int(convert_human_to_bytes(iostats[5])) / 1024 / 1024
    write = int(convert_human_to_bytes(iostats[6])) / 1024 / 1024
    graph['graph_throughput'] = {'values': [read, write]}

    return graph

@csrf_exempt
def graph_stats_json(request):
    return JSONResponse(graph_stats(1))

