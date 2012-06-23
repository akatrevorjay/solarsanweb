from celery.schedules import crontab
from celery.task import periodic_task, task, chord
from celery.task.base import PeriodicTask, Task
from celery.task.sets import subtask
from storage.models import Pool, Pool_IOStat, Dataset, Filesystem, Snapshot
from solarsan.utils import convert_bytes_to_human, convert_human_to_bytes
import datetime, time
from datetime import timedelta
from django.utils import timezone


class Check(object):
    """ Parent class for health checks """
    # check.enabled is checked once upon instantiation to see if this check
    #   is needed at all for this unit. By default, a check is not needed.
    enabled = False

    def __init__(self):
        pass

    def is_needed(self):
        """ Method to see if this check is needed at this point in time.
            Called once per health check. """
        return False

    def run(self):
        """ Method to do the actual check """
        pass


"""
   Device Failure and Recovery
       ZFS supports a rich set of mechanisms for handling device failure and data corrup‐
       tion. All metadata and data is checksummed, and ZFS automatically repairs bad data
       from a good copy when corruption is detected.

       In order to take advantage of these features, a pool must make use of some form of
       redundancy, using either mirrored or raidz groups. While ZFS supports running in a
       non-redundant  configuration,  where each root vdev is simply a disk or file, this
       is strongly discouraged. A single case of bit corruption can render some or all of
       your data unavailable.

       A  pool's  health status is described by one of three states: online, degraded, or
       faulted. An online pool has all devices operating normally. A degraded pool is one
       in which one or more devices have failed, but the data is still available due to a
       redundant configuration. A faulted pool has corrupted metadata,  or  one  or  more
       faulted devices, and insufficient replicas to continue functioning.

       The  health  of the top-level vdev, such as mirror or raidz device, is potentially
       impacted by the state of its associated vdevs, or component devices.  A  top-level
       vdev or component device is in one of the following states:

       DEGRADED    One  or  more  top-level vdevs is in the degraded state because one or
                   more component devices are offline. Sufficient replicas exist to  con‐
                   tinue functioning.

                   One or more component devices is in the degraded or faulted state, but
                   sufficient replicas exist to continue functioning. The underlying con‐
                   ditions are as follows:

                       o      The number of checksum errors exceeds acceptable levels and
                              the device is degraded as an indication that something  may
                              be wrong. ZFS continues to use the device as necessary.

                       o      The  number  of  I/O  errors exceeds acceptable levels. The
                              device could not be marked as  faulted  because  there  are
                              insufficient replicas to continue functioning.

       FAULTED     One  or  more  top-level  vdevs is in the faulted state because one or
                   more component devices are offline.  Insufficient  replicas  exist  to
                   continue functioning.

                   One  or  more  component devices is in the faulted state, and insuffi‐
                   cient replicas exist to continue functioning.  The  underlying  condi‐
                   tions are as follows:

                       o      The  device could be opened, but the contents did not match
                              expected values.

                       o      The number of I/O errors exceeds acceptable levels and  the
                              device is faulted to prevent further use of the device.

       OFFLINE     The  device  was  explicitly taken offline by the "zpool offline" com‐
                   mand.

       ONLINE      The device is online and functioning.

       REMOVED     The device was physically removed while the system was running. Device
                   removal  detection  is  hardware-dependent and may not be supported on
                   all platforms.

       UNAVAIL     The device could not be opened. If a pool is imported  when  a  device
                   was  unavailable, then the device will be identified by a unique iden‐
                   tifier instead of its path since the path was  never  correct  in  the
                   first place.

       If  a  device  is removed and later re-attached to the system, ZFS attempts to put
       the device online automatically. Device attach detection is hardware-dependent and
       might not be supported on all platforms.
"""

class Pool_Health(Check):
    """ Software - ZFS - Checks Pool health """
    #enabled = True
    def run(self):
        for p in Pool.objects.filter(health='ONLINE'):
            pass


class LSI_MegaCLI_RAID(Check):
    """ Hardware - HwRaid - Checks LSI MegaCLI for RAID Failures """
    #enabled = True
    def run(self):
        pass


class Check_Health(PeriodicTask):
    """ Cron job to periodically check the health of the SAN """
    #run_every = timedelta(minutes=30)
    run_every = timedelta(seconds=30)
    checks = {}

    def __init__(self, *args, **kwargs):
        # TODO Gather list of checks
        super(Check_Health, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        logging = self.get_logger(**kwargs)

        for key in self.checks.keys():
            pass

