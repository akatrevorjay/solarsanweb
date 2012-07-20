
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

urlpatterns = patterns('',
    #url(r'^posts/(?P<post_slug>[^/]+)/$', blogpost_resource), 
    #url(r'^other/(?P<username>[^/]+)/(?P<data>.+)/$', arbitrary_resource), 

    #url(r'^other/(?P<name>[^/]+)/(?P<data>.+)/$', arbitrary_resource),

    #url(r'^pool(\.(?P<emitter_format>.+))$$', PoolResource),
    #url(r'^dataset(\.(?P<emitter_format>.+))$$', DatasetResource),

    url(r'^cluster/probe(\.(?P<emitter_format>.+))$', ClusterProbeResource),
)

