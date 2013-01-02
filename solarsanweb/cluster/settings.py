#
# RPC
#

CLUSTER_RPC_PORT = 1787        # Port (1337 * 1.337)
CLUSTER_RPC_BIND = 'tcp://0.0.0.0:%d' % CLUSTER_RPC_PORT

#
# Discovery
#

CLUSTER_DISCOVERY_PORT = 1785
CLUSTER_DISCOVERY_INTERVAL = 60    # Scan for other nodes at this rate in seconds

#
# netbeacon discovery
#

# TODO Make key configurable, put it in the DB and in the UI.
CLUSTER_DISCOVERY_KEY = 'solarsan-key0'


#
# zmq discovery
#

CLUSTER_DISCOVERY_MSG_SIZE = 1
# TODO Make key configurable, put it in the DB and in the UI.
CLUSTER_DISCOVERY_INTERFACE = 'eth1'