from dajax.core.Dajax import Dajax
from dajaxice.decorators import dajaxice_register
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from solarsan.models import Dataset

@dajaxice_register
def dataset_info(request, dataset):
    """ Status: Gets dataset information """
    dajax = Dajax()
    d = Dataset.objects.get(name=dataset)
    
    dajax.assign('#dataset_info_title', 'innerHTML', dataset)
    dajax.assign('#dataset_info_menu', 'innerHTML',
                 render_to_string('solarsan/status_dataset_menu.html',
                                  {'dataset': d,
                                   }))
    dajax.assign('#dataset_info_content', 'innerHTML',
                 render_to_string('solarsan/status_dataset_info.html',
                                  {'dataset': d,
                                   }))    

    return dajax.json()

@dajaxice_register
def dataset_snapshots_list(request, dataset):
    """ Status: Lists snapshots of dataset """
    dajax = Dajax()
    d = Dataset.objects.get(name=dataset, type='filesystem')

    #dajax.assign('#dataset_info_title', 'innerHTML', dataset)
#    dajax.assign('#dataset_info_menu', 'innerHTML',
#                 render_to_string('solarsan/status_dataset_menu.html',
#                                  {'dataset': d,
#                                   }))
    dajax.assign('#dataset_info_content', 'innerHTML',
                 render_to_string('solarsan/status_snapshot_list.html',
                                  {'dataset': d,
                                   }))
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
