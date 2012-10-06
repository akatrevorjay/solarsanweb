from django.conf import settings

def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}

def site_styles(request):
    ctx = {}

    ctx['css_site'] = [
        # Can also be loaded by less.js from bootstrap's less files directly.
        'bootstrap/css/bootstrap.css',
        'bootstrap/css/bootstrap-responsive.css',

        '3rd/chosen/chosen/chosen.css',
        'css/nv.d3.css',
        '3rd/gritter/css/jquery.gritter.css',
        'css/font-awesome.css',
        'css/animate.css',
        #'css/bootstrap-toggle-buttons.css',
        'css/base.css',
    ]

    # Now using require.js, but this can be used in a pinch if testing something out.
    ctx['js_site'] = [
        # for now jQuery is handled without require-jquery
        'js/jquery.js',
        #'bootstrap/js/bootstrap.js',

    ]

    return ctx