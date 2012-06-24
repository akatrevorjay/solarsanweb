from django.shortcuts import render_to_response
from django.template import RequestContext

def home(request, *args, **kwargs):
    return render_to_response('scheduler/home.html',
        {'title': 'Scheduler',
            },
        context_instance=RequestContext(request))

