
from configure.models import Nic
from django.conf import settings
from storage.models import Pool


class ClusterRPC(object):
    def hostname(self):
        """Get hostname"""
        return settings.SERVER_NAME

    def interfaces(self):
        """Get interfaces and their addresses"""
        ifaces = Nic.list()
        ret = {}
        for iface_name, iface in ifaces.iteritems():
            for af, addrs in iface.addrs.iteritems():
                for addr in addrs:
                    if 'addr' not in addr or 'netmask' not in addr:
                        continue
                    if iface_name not in ret:
                        ret[iface_name] = {}
                    if af not in ret[iface_name]:
                        ret[iface_name][af] = []
                    ret[iface_name][af].append((addr['addr'], addr['netmask']))
        return ret

    def ping(self):
        """Ping Peer"""
        return True

    """
    Storage
    """

    def pools(self):
        """List Pools"""
        pools = [pool.name for pool in Pool.objects.all()]

    def is_pool_healthy(self, name):
        """Check if Pool is healthy"""
        pool = Pool.objects.get(name=name)
        return pool.is_healthy()