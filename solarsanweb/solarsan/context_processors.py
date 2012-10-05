from django.conf import settings

def raven_dsn(request):
    try:
        return {'raven_dsn': settings.RAVEN_CONFIG['dsn']}
    except:
        return {}

def site_styles(request):
    ctx = {}

    theme = ''

    ctx['css_site'] = [
        'bootstrap/css/bootstrap%s.css' % theme,
        'bootstrap/css/bootstrap-responsive.css',
        '3rd/chosen/chosen/chosen.css',
        'css/nv.d3.css',
        '3rd/gritter/css/jquery.gritter.css',
        'css/font-awesome.css',
        'css/animate.css',
        #'css/bootstrap-toggle-buttons.css',
        'css/base.css',
    ]

    ctx['js_site'] = [
        'js/jquery-1.8.0.js',
        'bootstrap/js/bootstrap.js',
        '3rd/d3/d3.v2.js',
        '3rd/cubism/cubism.v1.js',
        '3rd/nvd3/nv.d3.js',
        '3rd/gritter/js/jquery.gritter.js',
        '3rd/chosen/chosen/chosen.jquery.js',
        '3rd/raven-js/dist/raven-0.6pre.js',
        '3rd/bootbox/bootbox.js',
        'js/jquery.animate-colors-min.js',
        '3rd/underscore/underscore.js',
        '3rd/backbone/backbone.js',
        '3rd/backbone-relational/backbone-relational.js',
        'mustache/js/mustache-0.4.0-dev.js',
        'mustache/js/django.mustache.js',
        'js/backbone-tastypie.js',
        'js/base.js',
        #'js/chosen.jquery.js',
        #'3rd/flot/jquery.flot.js',
        #'3rd/flot/jquery.flot.time.js',
        #'3rd/flot/jquery.flot.crosshair.js',
        #'stick.js',
        #'js/jquery.toggle.buttons.js',
    ]

    return ctx