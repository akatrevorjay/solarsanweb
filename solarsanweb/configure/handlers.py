
from piston.handler import BaseHandler
from piston.utils import rc, throttle

from django_mongokit import get_database, connection
from configure.models import ClusterNode, NetworkInterfaceList

from django.conf import settings

from IPy import IP

class ClusterProbeHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        ifaces = NetworkInterfaceList()
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
        return {'hostname': settings.SERVER_NAME, 'interfaces': ret_ifaces}


