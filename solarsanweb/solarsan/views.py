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
    return render_to_response('solarsan/index.html',
        {'title': 'Status'},
        context_instance=RequestContext(request))

@csrf_exempt
def graph_stats(request):
    if request.GET.get('graph') == 'graph_utilization':
        graph = []
        
        zfs_dataset = 'rpool'
        zfs_lists = str(os.popen('/usr/sbin/zfs list -H -d 0 -t filesystem '+zfs_dataset).read()).splitlines()
        for i in zfs_lists:
            i = str(i).split()
            used = int(convert_human_to_bytes(i[1]))
            free = int(convert_human_to_bytes(i[2]))
            total = int(used + free)
            graph.append({'label': i[0]+' used', 'data': float(used / float(total) * 100) })
            graph.append({'label': i[0]+' free', 'data': float(free / float(total) * 100) })

    elif request.GET.get('graph') == 'graph_iops':
        iostats = str(os.popen('/usr/sbin/zpool iostat rpool | tail -n +4').read()).split()
        graph = [{'label': 'IOPs',
                  'data': [
                           ]
                  }]
    elif request.GET.get('graph') == 'graph_throughput':
        graph = [{'label': 'throughput',
                 'data': [[1,1],
                          [2,5],
                          [3,3]]}]
    else:
        return
    
    return JSONResponse(graph)

