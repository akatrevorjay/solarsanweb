
import logging
import os
import sys
import time

import socket
import zmq

from django.conf import settings
from . import tasks

import ethtool
from lru import LRUCacheDict


def get_local_ip_to(target):
    ret = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 8000))
        ret = s.getsockname()[0]
        s.close()
    except:
        pass
    return ret


class UDP(object):
    """simple UDP ping class"""
    handle = None   # Socket for send/recv
    broadcast = ''  # Broadcast address

    def __init__(self, port, address=None, broadcast=None):
        if broadcast is None:
            broadcast = '255.255.255.255'

        self.broadcast = broadcast
        self.port = port
        # Create UDP socket
        self.handle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Ask operating system to let us do broadcasts from socket
        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind UDP socket to local port so we can receive pings
        self.handle.bind(('', port))

    def send(self, buf):
        self.handle.sendto(buf, 0, (self.broadcast, self.port))

    def recv(self, n):
        buf, addrinfo = self.handle.recvfrom(n)
        print("Found peer %s:%d" % addrinfo)


class Beacon(UDP):
    address = None  # Our own address
    _local_ip_cache = None  # Cache of what our local IP is to target

    def __init__(self, interface, port, broadcast=None):
        self.address = ethtool.get_ipaddr(interface)
        self._local_ip_cache = LRUCacheDict(max_size=1024, expiration=3600)

        # if not broadcast:
        #    broadcast = ethtool.get_broadcast(interface)

        logging.info("Using iface '%s' address '%s:%d' broadcast '%s'",
                     interface, self.address, port, broadcast)
        super(Beacon, self).__init__(port, broadcast=broadcast)

    def recv(self, n):
        buf, addrinfo = self.handle.recvfrom(n)
        self.found_peer(addrinfo[0], buf)

    def send_ping(self):
        logging.debug("Pinging peers...")
        self.send('!')

    def found_peer(self, ip, buf):
        try:
            local_ip = self._local_ip_cache[ip]
        except KeyError:
            local_ip = self._local_ip_cache[ip] = get_local_ip_to(ip)
        from_self = local_ip == ip
        if from_self:
            return
        logging.debug("Got peer broadcast ip='%s', from_self='%s', buf='%s'", ip, from_self, buf)
        tasks.probe_node.delay(ip)


def main():
    beacon = Beacon(settings.CLUSTER_DISCOVERY_INTERFACE, settings.CLUSTER_DISCOVERY_PORT)

    poller = zmq.Poller()
    poller.register(beacon.handle, zmq.POLLIN)

    # Send first ping right away
    ping_at = time.time()

    while True:
        timeout = ping_at - time.time()
        if timeout < 0:
            timeout = 0
        try:
            events = dict(poller.poll(1000 * timeout))
        except KeyboardInterrupt:
            print("interrupted")
            break

        # Someone answered our ping
        if beacon.handle.fileno() in events:
            beacon.recv(settings.CLUSTER_DISCOVERY_MSG_SIZE)

        if time.time() >= ping_at:
            # Broadcast our beacon
            beacon.send_ping()
            ping_at = time.time() + settings.CLUSTER_DISCOVERY_INTERVAL

if __name__ == '__main__':
    main()