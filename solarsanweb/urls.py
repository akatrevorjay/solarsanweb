from django.conf.urls.defaults import patterns, include, url

# Jinja2 404/500s
#from coffin.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'solarsanweb.views.home', name='home'),
    url(r'^$', include('analytics.urls')),

    url(r'^status/', include('status.urls')),
    url(r'^configure/', include('configure.urls')),
    url(r'^storage/', include('storage.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^logs/', include('logs.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),          # Admin docs
    url(r'^admin/', include(admin.site.urls)),                              # Admin

    url(r'^', include('debug_toolbar_htmltidy.urls')),                      # DJDT HtmlTidy

    #url(r'^', include('solarsan.urls')),
    #url(r'^formtest/', include('formtest.urls')),

    url(r'^api/', include('api.urls')),
)


