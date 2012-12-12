from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import time

import sys
import zmq
from cluster.fsm import FSM
from cluster.models import Node, Peer
from storage.models import Pool


CLUSTER_ZMQ_HEARTBEAT_PORT = 5003
CLUSTER_ZMQ_API_PORT = 5001


class Command(BaseCommand):
    help = 'Run SolarSan Cluster ZMQ'
    args = 'primary'
    #label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        logging.info("Starting Cluster ZMQ..")
        print args, options

        primary = None
        if args:
            primary = bool(int(args[0]))
        print "primary=%s" % primary

        main()


def main():
    clustered_pools = [pool for pool in
                       Pool.objects_including_disabled.filter(is_clustered=True)]
    pool = clustered_pools[0]

    local = "tcp://*:%d" % CLUSTER_ZMQ_HEARTBEAT_PORT

    remote_host = "san1"
    remote = "tcp://%s:%d" % (remote_host, CLUSTER_ZMQ_HEARTBEAT_PORT)

    client = "tcp://*:%d" % CLUSTER_ZMQ_API_PORT

    fsm = FSM(True, local, remote)
    fsm.register_voter(client, zmq.ROUTER, echo)
    fsm.start()


def echo(socket, msg):
    """Echo service"""
    socket.send_multipart(msg)


if __name__ == '__main__':
    main()
