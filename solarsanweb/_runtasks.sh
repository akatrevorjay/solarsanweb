#!/bin/bash

_trevzfsprep.sh

while sleep 1; do python manage.py runtask cron_pool_iostats; done


