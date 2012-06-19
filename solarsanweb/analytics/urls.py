
from django.conf.urls import url, patterns, include

urlpatterns = patterns('analytics.views',
    (r'^(?:home)?$', 'home'),
    (r'^pool/graphs/(?P<pool>[A-z0-9_\-/]+)$', 'graphs'),
    (r'^render$', 'render'),
)

#urlpatterns += patterns('solarsan.ajax',
#    url(r'^graph/stats.json', 'graph_stats'),
#)

