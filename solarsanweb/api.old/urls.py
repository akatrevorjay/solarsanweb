
from django.conf.urls import url, patterns, include
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

#from api.handlers import BlogPostHandler, ArbitraryDataHandler

#auth = HttpBasicAuthentication(realm="My Realm")
#ad = { 'authentication': auth }

#blogpost_resource = Resource(handler=BlogPostHandler, **ad)
#arbitrary_resource = Resource(handler=ArbitraryDataHandler, **ad)

#from api.handlers import ArbitraryDataHandler
#arbitrary_resource = Resource(handler=ArbitraryDataHandler, **ad)

#from api.handlers import PoolHandler, DatasetHandler
#PoolResource = Resource(handler=PoolHandler, **ad)
#DatasetResource = Resource(handler=DatasetHandler, **ad)

from configure.handlers import ClusterProbeHandler
ClusterProbeResource = Resource(handler=ClusterProbeHandler)



from djangorestframework.resources import ModelResource
from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from storage.models import Pool, Filesystem, Volume, Snapshot


class SnapshotResource(ModelResource):
    model = Snapshot


class VolumeResource(ModelResource):
    model = Volume


class FilesystemResource(ModelResource):
    model = Filesystem


class PoolResource(ModelResource):
    model = Pool


urlpatterns = patterns('',
    #url(r'^posts/(?P<post_slug>[^/]+)/$', blogpost_resource),
    #url(r'^other/(?P<username>[^/]+)/(?P<data>.+)/$', arbitrary_resource),

    #url(r'^other/(?P<name>[^/]+)/(?P<data>.+)/$', arbitrary_resource),

    #url(r'^pool(\.(?P<emitter_format>.+))$$', PoolResource),
    #url(r'^dataset(\.(?P<emitter_format>.+))$$', DatasetResource),

    #url(r'^cluster/probe(\.(?P<emitter_format>.+))$', ClusterProbeResource),

    # django rest framework
    url(r'^pool/$', ListOrCreateModelView.as_view(resource=PoolResource)),
    url(r'^pool/(?P<name>[^/]+)/$', InstanceModelView.as_view(resource=PoolResource)),

    url(r'^filesystem/$', ListOrCreateModelView.as_view(resource=FilesystemResource)),
    url(r'^filesystem/(?P<name>[^/]+)/$', InstanceModelView.as_view(resource=FilesystemResource)),

    url(r'^volume/$', ListOrCreateModelView.as_view(resource=VolumeResource)),
    url(r'^volume/(?P<name>[^/]+)/$', InstanceModelView.as_view(resource=VolumeResource)),

    url(r'^snapshot/$', ListOrCreateModelView.as_view(resource=SnapshotResource)),
    url(r'^snapshot/(?P<name>[^/]+)/$', InstanceModelView.as_view(resource=SnapshotResource)),


)

