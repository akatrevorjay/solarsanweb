from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers

from utils import qdct_as_kwargs
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

import string, os, sys
from solarsan.utils import convert_human_to_bytes

def status(request):
    return render_to_response('solarsan/status.html',
        {'title': 'Status',
         'graph_stats': graph_stats()},
        context_instance=RequestContext(request))

def zfs_list():
    zfs_lists = str(os.popen('/usr/sbin/zfs list -H -d 0 -t filesystem '+zfs_dataset).read()).splitlines()
    for i in zfs_lists:
        i = str(i).split()
        used = int(convert_human_to_bytes(i[1]))
        free = int(convert_human_to_bytes(i[2]))
        total = int(used + free)
        graph['graph_utilization'] = {'values': [float(used / float(total) * 100), float(free / float(total) * 100)] }

def zpool_iostat(zfs_dataset, capture_length):
    return str(os.popen('/usr/sbin/zpool iostat \''+zfs_dataset+'\' '+str(capture_length)+' 2 | tail -n +5').read()).split()

def graph_stats():
    iostats = zpool_iostat('rpool', 2)
    
    graph = {}

    used = int(convert_human_to_bytes(iostats[1]))
    free = int(convert_human_to_bytes(iostats[2]))
    total = int(used + free)
    graph['graph_utilization'] = {'values': [float(used / float(total) * 100), float(free / float(total) * 100)] }
    
    iops_read = int(iostats[3])
    iops_write = int(iostats[4])
    graph['graph_iops'] = {'values': [iops_read, iops_write]}
    
    read = int(convert_human_to_bytes(iostats[5]))
    write = int(convert_human_to_bytes(iostats[5]))
    graph['graph_throughput'] = {'values': [read, write]}

    return graph

@csrf_exempt
def graph_stats_json(request):
    return JSONResponse(graph_stats())

