from django.conf.urls.defaults import patterns, include, url

# Jinja2 404/500s
#from coffin.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
#from mongoadmin import site

urlpatterns = patterns('',
    #url(r'^$', 'solarsanweb.views.home', name='home'),
    url(r'^$', include('analytics.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    url(r'^status/', include('status.urls')),
    url(r'^configure/', include('configure.urls')),
    url(r'^storage/', include('storage.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^logs/', include('logs.urls')),

    (r'^admin/', include('smuggler.urls')), # put it before admin url patterns (smuggler)

    (r'^admin/uwsgi/', include('uwsgi_admin.urls')),                        # uwsgi admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),          # Admin docs
    #url(r'^admin/', include(site.urls)),                                    # Admin (mongoadmin)
    url(r'^admin/', include(admin.site.urls)),                              # Admin

    url(r'^', include('debug_toolbar_htmltidy.urls')),                      # DJDT HtmlTidy

    #url(r'^', include('solarsan.urls')),
    #url(r'^formtest/', include('formtest.urls')),

    url(r'^api/v1/', include('api.urls')),
)


