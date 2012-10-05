from django.shortcuts import render_to_response
from django.template import RequestContext

from storage.models import Pool

def index(request, *args, **kwargs):
    pools = Pool.objects.all()
    return render_to_response('status/home.html',
        {'title': 'Status',
         'pools': pools,
            },
        context_instance=RequestContext(request))

