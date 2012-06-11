
from django.conf.urls import patterns, url, include
from django.views.generic import DetailView, ListView

from solarsan.models import Pool

urlpatterns = patterns('solarsan.views',
)

#urlpatterns += patterns('solarsan.ajax',
#    (r'^graph/stats.json', 'graph_stats'),
#)

