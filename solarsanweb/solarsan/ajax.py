from dajax.core.Dajax import Dajax
from dajaxice.decorators import dajaxice_register
from django.http import HttpResponseRedirect, HttpResponse

@dajaxice_register
def graph_utilization2(request):
    dajax = Dajax()
    dajax.assign('#graph_utilization td.free','innerHTML','75')
    dajax.assign('#graph_utilization td.used','innerHTML','25')
    return dajax.json()


