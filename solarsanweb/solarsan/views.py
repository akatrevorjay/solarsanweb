from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core import serializers

from utils import qdct_as_kwargs
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

from solarsan.utils import *
from solarsan.models import *

def status(request):
    """ Displays status of SAN """

    pools = Pool.objects.all()
    
    return render_to_response('solarsan/status.html',
        {'title': 'Status',
         'pools': pools},
        context_instance=RequestContext(request))

@csrf_exempt
def status_dataset_info(request, *args, **kwargs):
    """ Status: Gets dataset info """

    action = kwargs.get('action', request.GET.get('action'))
    dataset = kwargs.get('dataset', request.GET.get('dataset'))

    if action == "snapshots":
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

