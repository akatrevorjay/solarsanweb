from django.conf import settings
from solarsan.forms import LoginForm


def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}


def login_form(request):
    return {'login_form': LoginForm}


def site_styles(request):
    ctx = {}

    #
    # CSS
    #

    ctx['css_site'] = [
        # Can also be loaded by less.js from bootstrap's less files directly.
        'bootstrap/css/bootstrap.css',
        'bootstrap/css/bootstrap-responsive.css',

        #'3rd/chosen/chosen/chosen.css',
        'css/nv.d3.css',
        '3rd/gritter/css/jquery.gritter.css',
        'css/font-awesome.css',
        'css/animate.css',
        #'css/bootstrap-toggle-buttons.css',
        #'css/datepicker.css',
        #'css/bootstrap-editable.css',

        'css/base.css',
    ]

    #
    # Javascript
    #

    js_site_pre = [
        'jquery',
        'bootstrap',
        #'bootstrap-datepicker',
        #'bootstrap-editable',
        #'chosen',
        'jquery.gritter',

        'd3',
        'cubism',
        'nvd3',

        'mustache',
        'django.mustache',

        #'underscore',
        #'backbone',
        #'backbone-tastypie',
        #'backbone-relational',

        'base',
        'pool/analytics',
        'debug_toolbar',
    ]

    #
    # Fix up javascript URLs
    #

    js_tmpl = {
        'static': settings.STATIC_URL,
        'static_js': '%sjs/' % settings.STATIC_URL,
        'bootstrap': '%sbootstrap/js/' % settings.STATIC_URL,
        'ext_js': '.js',
    }

    ctx['js_site'] = js_site = []
    for j in js_site_pre:
        k = '%(js)s'
        # bootstrap has a special path
        if j == 'bootstrap' or j.startswith('bootstrap/'):
            k = '%(bootstrap)s' + k
        # If relative, make absolute with default path
        elif not j.startswith('/'):
            k = '%(static_js)s' + k

        # Add .js if not there already
        if not j.endswith('.js'):
            k += '%(ext_js)s'

        # Replace variables with js_tmpl kvs
        js_tmpl['js'] = j
        j = k % js_tmpl

        js_site.append(j)

    return ctx
