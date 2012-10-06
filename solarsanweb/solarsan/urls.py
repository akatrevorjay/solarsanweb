
from django.conf.urls.defaults import patterns, url, include
#from django.views import generic
from django.conf import settings

urlpatterns = patterns('solarsan.views',
    url(r'^base_site.js', 'base_site_js', name='base-site-js'),
)

