from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
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
def graph_stats_json(request):
    return JSONResponse(graph_stats(10))

