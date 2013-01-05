
import logging

from django.conf import settings
from . import client

import zerorpc


def get_client(host):
    # FIXME c.close() does not seem to do anything as the timeout still happens.
    # As a temporary fix for dev'ing, it's now set to one hour.
    # This could become a problem if too many connections are opened...
    c = zerorpc.Client(heartbeat=1, timeout=3600)
    c.connect('tcp://%s:%d' % (host, settings.CLUSTER_RPC_PORT))
    return c


def get_client_cached(host):
    if not hasattr(client, '_CLIENTS'):
        setattr(client, '_CLIENTS', {})
    clients = client._CLIENTS

    if not host in clients:
        clients[host] = get_client(host)

    return clients.get(host, None)


def run_server():
    logging.info("Starting Cluster RPC Server..")
    from . import server
    s = zerorpc.Server(server.ClusterRPC())
    s.bind(settings.CLUSTER_RPC_BIND)
    s.run()