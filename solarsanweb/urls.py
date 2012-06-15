from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'solarsanweb.views.home', name='home'),

    # SolarSAN
    #url(r'^$', include('dashboard.urls')),
    url(r'^$', include('dashboard.urls')),

    url(r'^solarsan/', include('solarsan.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^configure/', include('configure.urls')),
    url(r'^cluster/', include('cluster.urls')),
    url(r'^backup/', include('backup.urls')),
    url(r'^scheduler/', include('scheduler.urls')),
    url(r'^pools/', include('pools.urls')),
    url(r'^datasets/', include('datasets.urls')),
    url(r'^logs/', include('logs.urls')),
    url(r'^analytics/', include('analytics.urls')),


    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    #url(r'^', include('solarsan.urls')),
)

