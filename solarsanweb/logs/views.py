from dj import render_to_response, generic, http, RequestContext
from django.conf import settings
import logging
import json
from os.path import getsize, isfile

from .models import LogEntry


def home(request, *args, **kwargs):
    logs = LogEntry.objects.order_by('-DATE')[:100]
    return render_to_response('logs/home.html',
        {'entries': logs,
            },
        context_instance=RequestContext(request))


class LogListView(generic.ListView):
    template_name = 'logs/logtail_list.html'

    @property
    def queryset(self):
        for log, filename in settings.LOGTAIL_FILES.iteritems():
            if isfile(filename):
                yield (log, filename)

    def get_context_data(self, **kwargs):
        context = super(Loggeneric.ListView, self).get_context_data(**kwargs)
        context['update_interval'] = 1000
        return context


class LogTailView(generic.View):
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
