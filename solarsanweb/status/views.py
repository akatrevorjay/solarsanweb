
from dj import RequestContext, render_to_response, generic

from . import forms
#from . import tasks
import solarsan.tasks

def index(request, *args, **kwargs):
    return render_to_response('status/home.html',
        {'title': 'Status',
            },
        context_instance=RequestContext(request))


class ShutdownView(generic.edit.FormView):
    template_name = 'status/shutdown.html'
    form_class = forms.ShutdownForm

    def form_valid(self, form):
        solarsan.tasks.shutdown.delay()
        #self.success_url = reverse
        return super(ShutdownView, self).form_valid(form)

shutdown = ShutdownView.as_view()


class RebootView(generic.edit.FormView):
    template_name = 'status/reboot.html'
    form_class = forms.RebootForm

    def form_valid(self, form):
        solarsan.tasks.reboot.delay()
        #self.success_url = reverse
        return super(RebootView, self).form_valid(form)

reboot = RebootView.as_view()
