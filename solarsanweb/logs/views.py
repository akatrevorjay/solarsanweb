from django.shortcuts import render_to_response

from django.views.generic import View, ListView
from django.template import RequestContext
from django import http
from django.conf import settings

import logging
import json
from os.path import getsize, isfile



import mongoengine

class LogEntry(mongoengine.DynamicDocument):
    meta = {'collection': 'messages',
            'db_alias': 'syslog',
            'max_size': 1024 * 1024 * 256,
            'allow_inheritance': False,
            }




def home(request, *args, **kwargs):
    logs = LogEntry.objects.all()[:100]
    return render_to_response('logs.html',
        {'title': 'Logs',
            },
        context_instance=RequestContext(request))

class LogListView(ListView):
    template_name = 'logs/logtail_list.html'

    @property
    def queryset(self):
        for log, filename in settings.LOGTAIL_FILES.iteritems():
            if isfile(filename):
                yield (log, filename)

    def get_context_data(self, **kwargs):
        context = super(LogListView, self).get_context_data(**kwargs)
        context['update_interval'] = 1000
        return context

class LogTailView(View):
    """
    Returns JSON of the form::

        {
            "starts": "0",
            "data": "LOGFILEHERE"
            "ends": "3284",
        }
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = {}
        seek_to = int(self.kwargs.get('seek_to', '0'))
        try:
            log_file_id = self.kwargs.get('logfile', '')
            log_file = settings.LOGTAIL_FILES[log_file_id]
        except KeyError:
            raise http.Http404('No such log file')

        try:
            file_length = getsize(log_file)
        except OSError:
            raise http.Http404('Cannot access file')

        if seek_to > file_length:
            seek_to = file_length

        try:
            context['log'] = file(log_file, 'r')
            context['log'].seek(seek_to)
            context['starts'] = seek_to
        except IOError:
            raise http.Http404('Cannot access file')

        return context

    def iter_json(self, context):
        yield '{"starts": "%d",' \
               '"data": "' % context['starts']

        while True:
            line = context['log'].readline()
            if line:
                yield json.dumps(line).strip(u'"')
            else:
                yield '", "ends": "%d"}' % context['log'].tell()
                context['log'].close()
                return

    def render_to_response(self, context):
        return http.HttpResponse(
            self.iter_json(context),
            content_type='application/json'
        )


