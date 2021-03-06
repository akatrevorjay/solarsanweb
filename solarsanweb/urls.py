from django.conf.urls.defaults import patterns, include, url

# Jinja2 404/500s
#from coffin.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

site = admin.site
#from django_mongoengine.admin import site

#from django_logtail import urls as logtail_urls


urlpatterns = patterns('',

    #(r'^accounts/', include('allauth.urls')),
    #url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='account-login'),
    #url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    #url(r'^accounts/', include('django.contrib.auth.urls'), name='account'),
    #url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    #url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='account-reset-password'),
    #(r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    #(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    #(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),

    url(r'^$', include('status.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^configure/', include('configure.urls')),
    url(r'^cluster/', include('cluster.urls')),
    url(r'^logs/', include('logs.urls')),
    url(r'^', include('solarsan.urls')),
    url(r'^status/', include('status.urls')),
    url(r'^storage/', include('storage.urls')),

    url(r'^api/v1/', include('api.urls'), name='api'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #url(r'^restframework', include('djangorestframework.urls', namespace='djangorestframework')),

    #url(r'^formtest/', include('formtest.urls')),

    #url(r'^admin/django_logtail/', include(logtail_urls)),
    #(r'^admin/', include('smuggler.urls')), # put it before admin url patterns (smuggler)
    #(r'^admin/uwsgi/', include('uwsgi_admin.urls')),                        # uwsgi admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),          # Admin docs
    url(r'^admin/', include(site.urls)),                                    # Admin (django-mongoengine/mongoadmin)
    #url(r'^admin/', include(admin.site.urls)),                              # Admin
)


