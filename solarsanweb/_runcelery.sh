#!/bin/bash

# --autoscale=10,1
# -P processes (default), eventlet, gevent, solo, threads
# --purge
#while sleep 1; do 
    ./manage.py celeryd -E -B --autoreload --traceback -v 2 -l DEBUG -P threads
#done

