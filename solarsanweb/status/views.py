
from dj import RequestContext, render_to_response, generic
import sh

from . import forms


def index(request, *args, **kwargs):
    return render_to_response('status/home.html',
        {'title': 'Status',
            },
        context_instance=RequestContext(request))


class RebootView(generic.edit.FormView):
    template_name = 'status/reboot.html'
    form_class = forms.RebootForm

    def form_valid(self, form):
        sh.reboot()
        #self.success_url = reverse
        return super(RebootView, self).form_valid(form)

reboot = RebootView.as_view()
