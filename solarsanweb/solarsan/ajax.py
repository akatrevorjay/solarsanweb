from dajax.core.Dajax import Dajax
from dajaxice.decorators import dajaxice_register
from django.http import HttpResponseRedirect, HttpResponse

from OpenFlashChart import Chart

@dajaxice_register
def graph_utilization2(request):
    dajax = Dajax()
    dajax.assign('#graph_utilization td.free','innerHTML','75')
    dajax.assign('#graph_utilization td.used','innerHTML','25')
    return dajax.json()

def graph_utilization(request):
    chart = Chart()
    chart.title.text = "Utilization"
    chart.bg_colour = "#ffffff"
    #chart.on_show = False

    e1 = Chart()
    #e1.start_angle = "n"
    #e1.animation_offset = 0
        
    e1.type = "pie"
    e1.values = [{'label': 'Free', 'value': 75},
                 {'label': 'Used', 'value': 25},
                ]
    e1.colours = ['#11bb11', '#bb1111']
    e1.alpha = 0.7

    e1.tip = "#percent#"

    #e1.on_show = False
    #e1.on_show = [False]
    #e1.on_show = ['false']
    #e1.on_show = 'false'
    #e1.on_show = [{'type': ''}]

    #e1.animate = [{'type': 'fade'},]
    #e1.animate = [{'type': 'fade'},]
    #e1.animate = []
    
    e1.gradient_fill = "true"
    e1.radius = 50

    chart.elements = [e1]    
    return HttpResponse(chart.create())

def graph_throughput(request):
    chart = Chart()
    chart.title.text = "Throughput"
    chart.bg_colour = "#ffffff"
    
    e1 = Chart()
    e1.type = "pie"
    e1.values = [{'label': 'Read', 'value': 25},
                 {'label': 'Write', 'value': 75},
                ]
    e1.colours = ['#11bb11', '#bb1111']
    e1.alpha = 0.7
    e1.start_angle = 0
    #e1.tip = "#percent#"
    e1.animate = [{'type': 'fade'},]
    e1.gradient_fill = "true"   
    e1.radius = 50
    
    chart.elements = [e1]
    return HttpResponse(chart.create())

def graph_iops(request):
    chart = Chart()
    chart.title.text = "IOPs"
    chart.bg_colour = "#ffffff"
    
    e1 = Chart()
    e1.type = "pie"
    e1.values = [{'label': 'Read', 'value': 75},
                 {'label': 'Write', 'value': 25},
                ]
    e1.colours = ['#11bb11', '#bb1111']
    e1.alpha = 0.7
    e1.start_angle = 0
    #e1.tip = "#percent#"
    e1.animate = [{'type': 'fade'},]
    e1.gradient_fill = "true"   
    e1.radius = 50
    
    chart.elements = [e1]    
    return HttpResponse(chart.create())

