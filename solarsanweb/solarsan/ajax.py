from dajax.core.Dajax import Dajax
from dajaxice.decorators import dajaxice_register
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from solarsan.utils import zfs_list

@dajaxice_register
def status_dataset(request, dataset):
    dajax = Dajax()
    datasets = zfs_list()
    
    dajax.assign('#dataset_info', 'innerHTML',
                 render_to_string('solarsan/status_dataset_info.html',
                                  {'dataset': datasets[dataset],
                                   'tempjson': simplejson.dumps(datasets[dataset], sort_keys=True, indent=4) }))
    
    return dajax.json()

@dajaxice_register
def graph_utilization2(request):
    dajax = Dajax()
    dajax.assign('#graph_utilization td.free','innerHTML','75')
    dajax.assign('#graph_utilization td.used','innerHTML','25')
    return dajax.json()

from dajaxice.core import dajaxice_functions
from django.utils import simplejson
def myexample(request):
    return simplejson.dumps({'message':'Hello World'})
dajaxice_functions.register(myexample)
