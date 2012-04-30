import jinja2

from jingo import register
import chartit.templatetags.chartit

@register.filter
def load_charts(*args):
    """ Writes out django-chartit charts; this is a wrapper around the django templatetag """
    return jinja2.Markup(chartit.templatetags.chartit.load_charts(*args))

