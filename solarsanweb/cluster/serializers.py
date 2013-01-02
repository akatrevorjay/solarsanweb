#from django.forms import widgets
from rest_framework import serializers


'''
class ClusterProbeSerializer(serializers.Serializer):
    hostname = serializers.Field()
    interfaces = serializers.Field()

    #def restore_object(self, attrs, instance=None):
    #    if instance:
    #        return instance
    #    return dict()
'''


'''
class ClusterPingSerializer(serializers.Serializer):
    pong = serializers.Field()
'''


class ClusteredPoolHeartbeatSerializer(serializers.Serializer):
    pools = serializers.Field()
