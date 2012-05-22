from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

# Dajaxice
#from django.conf import settings
#from dajaxice.core import dajaxice_autodiscover
#dajaxice_autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'solarsanweb.views.home', name='home'),
    #url(r'^polls/', include('polls.urls')),

    # Dajaxice
    #(r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),

    # SolarSAN
    url(r'^$', include('solarsan.urls')),
    url(r'^solarsan/', include('solarsan.urls')),
    #url(r'^bootstrap_example/', include('bootstrap_example.root.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
)
