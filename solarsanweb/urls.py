from django.conf.urls.defaults import patterns, include, url

# Jinja2 404/500s
#from coffin.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
#from mongoadmin import site

import time
#from statsd import StatsClient
#statsd = StatsClient()
from django_statsd.clients import statsd
start = time.time()
time.sleep(3)

# You must convert to milliseconds:
dt = int((time.time() - start) * 1000)
statsd.timing('slept', dt)

urlpatterns = patterns('',
    #url(r'^$', 'solarsanweb.views.home', name='home'),
    url(r'^$', include('analytics.urls')),

    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    (r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),

    url(r'^status/', include('status.urls')),
    url(r'^configure/', include('configure.urls')),
    url(r'^storage/', include('storage.urls')),
    url(r'^logs/', include('logs.urls')),

    url(r'^analytics/', include('analytics.urls')),
    url(r'^services/timing/', include('django_statsd.urls')),

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


