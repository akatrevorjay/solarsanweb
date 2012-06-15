import jinja2
from jingo import register

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

