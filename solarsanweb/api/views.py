
from rest_framework import status
from rest_framework import renderers
from rest_framework import generics, mixins
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework import permissions

from django.contrib.auth.models import User, Group
import storage.models
from api import serializers


@api_view(['GET'])
def api_root(request, format=None):
    """The entry endpoint of our API.
    """
    return Response({
        'users': reverse('user-list', request=request),
        'groups': reverse('group-list', request=request),
        'pools': reverse('pool-list', request=request),
    })


class UserList(generics.ListCreateAPIView):
    """API endpoint that represents a list of users.
    """
    model = User
    serializer_class = serializers.UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint that represents a single user.
    """
    model = User
    serializer_class = serializers.UserSerializer



from api.serializers import UserSerializer


class UserList2(generics.ListAPIView):
    model = User
    serializer_class = UserSerializer


class UserInstance2(generics.RetrieveAPIView):
    model = User
    serializer_class = UserSerializer



class GroupList(generics.ListCreateAPIView):
    """API endpoint that represents a list of groups.
    """
    model = Group
    serializer_class = serializers.GroupSerializer


class GroupDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint that represents a single group.
    """
    model = Group
    serializer_class = serializers.GroupSerializer



class PoolList(generics.ListCreateAPIView):
    model = storage.models.Pool
    serializer_class = serializers.PoolSerializer


class PoolDetail(generics.RetrieveUpdateDestroyAPIView):
    model = storage.models.Pool
    serializer_class = serializers.PoolSerializer


@api_view(['GET', 'POST'])
def pool_list(request, format=None):
    """
    List all pools, or create a new pool.
    """
    if request.method == 'GET':
        pools = storage.models.Pool.objects.all()
        serializer = serializers.PoolSerializer(pools)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = serializers.PoolSerializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from configure.models import NetworkInterface
from django.conf import settings
from IPy import IP


class ClusterProbe(object):
    interfaces = None
    hostname = None


@api_view(['GET'])
def cluster_probe(request, format=None):
    """Cluster probe API"""
    if request.method == 'GET':
        ifaces = NetworkInterface.list()
        ret_ifaces = {}
        for iface_name, iface in ifaces.iteritems():
            for af, addrs in iface.addrs.iteritems():
                for addr in addrs:
                    if 'addr' not in addr or 'netmask' not in addr:
                        continue
                    if iface_name not in ret_ifaces:
                        ret_ifaces[iface_name] = {}
                    if af not in ret_ifaces[iface_name]:
                        ret_ifaces[iface_name][af] = []
                    ret_ifaces[iface_name][af].append( (addr['addr'], addr['netmask']) )
        ret = ClusterProbe()
        ret.hostname = settings.SERVER_NAME
        ret.interfaces = ret_ifaces
        #ret = {'hostname': settings.SERVER_NAME, 'interfaces': ret_ifaces}
        serializer = serializers.ClusterProbeSerializer(ret)
        return Response(serializer.data)





#class FilesystemList(generics.ListCreateAPIView):
#    model = storage.models.Filesystem
#    serializer_class = serializers.FilesystemSerializer


#class FilesystemDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = storage.models.Filesystem
#    serializer_class = serializers.FilesystemSerializer


#class VolumeList(generics.ListCreateAPIView):
#    model = storage.models.Volume
#    serializer_class = serializers.VolumeSerializer


#class VolumeDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = storage.models.Volume
#    serializer_class = serializers.VolumeSerializer


#class SnapshotList(generics.ListCreateAPIView):
#    model = storage.models.Snapshot
#    serializer_class = serializers.SnapshotSerializer


#class SnapshotDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = storage.models.Snapshot
#    serializer_class = serializers.SnapshotSerializer


#class TargetList(generics.ListCreateAPIView):
#    model = storage.models.Target
#    serializer_class = serializers.TargetSerializer


#class TargetDetail(generics.RetrieveUpdateDestroyAPIView):
#    model = storage.models.Target
#    serializer_class = serializers.TargetSerializer


#
# restframework examples:
#

#from api.serializers import SnippetSerializer


#@api_view(['GET', 'POST'])
#def snippet_list(request, format=None):
#    """
#    List all snippets, or create a new snippet.
#    """
#    if request.method == 'GET':
#        snippets = Snippet.objects.all()
#        serializer = SnippetSerializer(snippets)
#        return Response(serializer.data)

#    elif request.method == 'POST':
#        serializer = SnippetSerializer(data=request.DATA)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data, status=status.HTTP_201_CREATED)
#        else:
#            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#@api_view(['GET', 'PUT', 'DELETE'])
#def snippet_detail(request, pk, format=None):
#    """
#    Retrieve, update or delete a snippet instance.
#    """
#    try:
#        snippet = Snippet.objects.get(pk=pk)
#    except Snippet.DoesNotExist:
#        return Response(status=status.HTTP_404_NOT_FOUND)

#    if request.method == 'GET':
#        serializer = SnippetSerializer(snippet)
#        return Response(serializer.data)

#    elif request.method == 'PUT':
#        serializer = SnippetSerializer(snippet, data=request.DATA)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data)
#        else:
#            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#    elif request.method == 'DELETE':
#        snippet.delete()
#        return Response(status=status.HTTP_204_NO_CONTENT)

##
## non-mixin non-generic CBV
##

#class SnippetList(APIView):
#    """
#    List all snippets, or create a new snippet.
#    """
#    def get(self, request, format=None):
#        snippets = Snippet.objects.all()
#        serializer = SnippetSerializer(snippets)
#        return Response(serializer.data)

#    def post(self, request, format=None):
#        serializer = SnippetSerializer(data=request.DATA)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data, status=status.HTTP_201_CREATED)
#        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#class SnippetDetail(APIView):
#    """
#    Retrieve, update or delete a snippet instance.
#    """
#    def get_object(self, pk):
#        try:
#            return Snippet.objects.get(pk=pk)
#        except Snippet.DoesNotExist:
#            raise Http404

#    def get(self, request, pk, format=None):
#        snippet = self.get_object(pk)
#        serializer = SnippetSerializer(snippet)
#        return Response(serializer.data)

#    def put(self, request, pk, format=None):
#        snippet = self.get_object(pk)
#        serializer = SnippetSerializer(snippet, data=request.DATA)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data)
#        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#    def delete(self, request, pk, format=None):
#        snippet = self.get_object(pk)
#        snippet.delete()
#        return Response(status=status.HTTP_204_NO_CONTENT)

##
## mixins
##

#class SnippetList2(mixins.ListModelMixin,
#                   mixins.CreateModelMixin,
#                   generics.MultipleObjectAPIView):
#    model = Snippet
#    serializer_class = SnippetSerializer

#    def get(self, request, *args, **kwargs):
#        return self.list(request, *args, **kwargs)

#    def post(self, request, *args, **kwargs):
#        return self.create(request, *args, **kwargs)


#class SnippetDetail2(mixins.RetrieveModelMixin,
#                     mixins.UpdateModelMixin,
#                     mixins.DestroyModelMixin,
#                     generics.SingleObjectAPIView):
#    model = Snippet
#    serializer_class = SnippetSerializer

#    def get(self, request, *args, **kwargs):
#        return self.retrieve(request, *args, **kwargs)

#    def put(self, request, *args, **kwargs):
#        return self.update(request, *args, **kwargs)

#    def delete(self, request, *args, **kwargs):
#        return self.destroy(request, *args, **kwargs)

##
## generics
##

#from api.permissions import IsOwnerOrReadOnly


#class SnippetList3(generics.ListCreateAPIView):
#    model = Snippet
#    serializer_class = SnippetSerializer
#    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
#                          IsOwnerOrReadOnly)

#    def pre_save(self, obj):
#        obj.owner = self.request.user


#class SnippetDetail3(generics.RetrieveUpdateDestroyAPIView):
#    model = Snippet
#    serializer_class = SnippetSerializer
#    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
#                          IsOwnerOrReadOnly)

#    def pre_save(self, obj):
#        obj.owner = self.request.user


#class SnippetHighlight(generics.SingleObjectAPIView):
#    model = Snippet
#    renderer_classes = (renderers.StaticHTMLRenderer,)

#    def get(self, request, *args, **kwargs):
#        snippet = self.get_object()
#        return Response(snippet.highlighted)



