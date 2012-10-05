"""
Helper functions to be used with Django and Jingo
"""
from django.utils.safestring import mark_safe
import re
import jinja2
from jingo import register
#from coffin import template
register = template.Library()


@register.filter
def flotjson(graph, container, **kwargs):
    """ Writes out JSON for a flot graph"""

    out=[]

    if kwargs.get('wrapper', True):
        out.append('<script id="source" language="javascript" type="text/javascript">')
        out.append('$(function () {')

    out.append('$.plot($("#%s"), %s, %s);' %
               (container, graph.series_json, graph.options_json) )


    if kwargs.get('wrapper', True):
        out.append('});')
        out.append('</script>')

    return jinja2.Markup("\n".join(out))