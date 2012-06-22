from django.shortcuts import render_to_response
from django.template import RequestContext

from solarsan.models import Pool

def home(request, *args, **kwargs):
    pools = Pool.objects.all()
    return render_to_response('status.html',
        {'title': 'Status',
         'pools': pools,
            },
        context_instance=RequestContext(request))

