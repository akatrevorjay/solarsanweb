
from django.conf.urls import patterns, url, include
from django.views.generic import DetailView, ListView

from solarsan.models import Filesystem

urlpatterns = patterns('datasets.views',
    (r'^detail/(?P<slug>[A-z0-9_\-/]+)$', DetailView.as_view(
        model=Filesystem,
        context_object_name='dataset_detail',
        slug_field='name',
        template_name='solarsan/dataset_detail.html',
        )),
)

