
from django.conf.urls import url, patterns, include

urlpatterns = patterns('analytics.views',
    url(r'^$', 'home', name='analytics'),
    url(r'^detail/(?P<name>[A-z0-9_\-]+)$', 'home', name='analytics-detail'),
    url(r'^detail/(?P<name>[A-z0-9_\-]+)/(?P<time_window>[0-9]+)$', 'home', name='analytics-detail-time_window'),
    url(r'^render$', 'render', name='analytics-render'),
)
