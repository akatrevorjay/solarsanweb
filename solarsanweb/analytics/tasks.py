from celery.task import periodic_task, task
from celery.task.base import PeriodicTask, Task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from storage.models import Pool, Pool_IOStat
from solarsan.utils import convert_human_to_bytes
import os, time
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

import zfs

#from kstats import KStats as kstats
import kstats
from pyrrd.backend import bindings
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, ColorAttributes, Graph
from pyrrd.rrd import DataSource, RRA, RRD
from django_statsd.clients import statsd

"""
Per-File IO Monitor
"""

from storage.models import Filesystem
import iterpipes

#class File_IO_Monitor(PeriodicTask):
class File_IO_Monitor(Task):
    #run_every = timedelta(seconds=10)
    def run(self, *args, **kwargs):
        events = list(kwargs.get('events', ['access', 'modify', 'create', 'delete']))
        capture_length = str(int(kwargs.get('capture_length', 10)))

        # TODO Don't hardcode this. Get list of Pool's filesystem mountpoints, or just run this once per dataset, all at once per dataset mountpoint.
        watches = list(kwargs.get('watches', ['/dpool/tmp']))

        filesystem_map = dict([(f[0], {'name': f[1], 'id': f[2]}) for f in Filesystem.objects.values_list('mountpoint', 'name', 'id')])
        filesystem_map_keys = filesystem_map.keys()
        filesystem_map_keys.sort()
        filesystem_map_keys.reverse()

        # Initial command
        cmd = 'inotifywatch -r -t {}'
        cargs = [capture_length]
        # Add events
        cmd += ' '+' '.join([('-e {}') for i in range(len(events))])
        cargs += events
        # Add watches
        cmd += ' '+' '.join([('{}') for i in range(len(watches))])
        cargs += watches
        # Nullify stderr
        cmd += ' '+'2>/dev/null'

        #print 'cmd=%s cargs=%s' % (cmd, cargs)
        data = {}
        header = []
        for line in iterpipes.run(iterpipes.linecmd(cmd, *cargs)):
            line = line.rstrip('\n')
            if len(header) == 0:
                # always fields: total, filename
                header = str(line).split()
                continue
            line = dict(zip(header, str(line).split()))
            filename = line.pop('filename')

            filesystem = None
            for fs in filesystem_map_keys:
                if filename.startswith(fs):
                    filesystem = filesystem_map[fs]
                    break
            if filesystem:
                data[filesystem['name']] = line
            else:
                #logger.warning('Got bad result from IO Monitor: "%s"', line)
                print 'line=%s' % line
        print "data=%s" % data


#
# pure python version, ended up being rather slow compared to parsing inotifywatch for obvious reasons..
#
# Plan is to duplicate the functionality of while sleep 1; do inotifywatch -t 10 -r /gvol0; done
# But instead do it in code and track it over time.
#

import pyinotify

class File_IO_Monitor_Event_Handler_Py(pyinotify.ProcessEvent):
    abbacus = {}
    totals = {}
    totals_wd = {}
    #def __init__(self, *args, **kwargs):
    #    super(File_IO_Monitor_Event_Handler_Py, self).__init__(*args, **kwargs)
    def process_default(self, event):
        #print "event: %s path: %s mask: %s" % (event.maskname, event.pathname, event.mask)
        #self.last_event = event

        if not event.wd in self.abbacus:
            self.abbacus[event.wd] = {}
        if not event.pathname in self.abbacus[event.wd]:
            self.abbacus[event.wd][event.pathname] = {}
        if not event.mask in self.abbacus[event.wd][event.pathname]:
            self.abbacus[event.wd][event.pathname][event.mask] = 0
        self.abbacus[event.wd][event.pathname][event.mask] += 1

        if not event.mask in self.totals:
            self.totals[event.mask] = 0
        self.totals[event.mask] += 1

        if not event.wd in self.totals_wd:
            self.totals_wd[event.wd] = {}
        if not event.mask in self.totals_wd[event.wd]:
            self.totals_wd[event.wd][event.mask] = 0
        self.totals_wd[event.wd][event.mask] += 1

#class File_IO_Monitor(PeriodicTask):
class File_IO_Monitor_Py(Task):
    #run_every = timedelta(seconds=10)
    def run(self, timeout=30, *args, **kwargs):
        if not hasattr(self, 'notifier'):
            self.wm = pyinotify.WatchManager()
            self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_ACCESS | pyinotify.IN_MODIFY
            #self.mask = pyinotify.ALL_EVENTS
            self.handler = File_IO_Monitor_Event_Handler_Py()
            # Internally, 'handler' is a callable object which on new events will be called like this: handler(new_event)
            self.wdd = self.wm.add_watch('/dpool/bricks', self.mask, rec=True, auto_add=True)
            self.notifier = pyinotify.Notifier(self.wm, self.handler, timeout=timeout, read_freq=5)
        self.notifier.process_events()
        while self.notifier.check_events():
            self.notifier.read_events()
            self.notifier.process_events()

        #self.abbacus = self.handler.abbacus.copy()
        #self.handler.abbacus.clear()
        #print self.abbacus

        #key = 'IN_ACCESS'
        #abbs_key = dict(filter(lambda (x,y): key in y, self.handler.abbacus.items()))
        #abbs_key_sorted = sorted(abbs_attrib.iterkeys(), key=lambda k: abbs_attrib[k][key])
        #abbs_key = dict([(x,y[key]) for x,y in self.abbacus.items() if key in y])


#
# Using self-patched watchdog library
#

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# TODO Red/black balanced tree algo:
#import bintrees

class File_IO_Monitor_Event_Handler_Py2(FileSystemEventHandler):
    abbacus = {}
    def on_any_event(self, event):
        if event.is_directory:
            return
        if not event.src_path in self.abbacus:
            self.abbacus[event.src_path] = {}
        if not event.event_type in self.abbacus[event.src_path]:
            self.abbacus[event.src_path][event.event_type] = 0
        self.abbacus[event.src_path][event.event_type]+=1
        print "event: %s path: %s" % (event.event_type, event.src_path)
        print "events: %s" % self.abbacus


#class File_IO_Monitor(PeriodicTask):
class File_IO_Monitor_Py2(Task):
    #run_every = timedelta(seconds=10)
    def run(self, *args, **kwargs):
        if not hasattr(self, 'observer'):
            event_handler = File_IO_Monitor_Event_Handler_Py2()
            self.observer = Observer()
            self.observer.schedule(event_handler, path='/tmp/montest', recursive=True)
            self.observer.start()


"""
Pool IOStats
"""

class Pool_IOStats_Populate(PeriodicTask):
    """ Periodic task to log iostats per pool to db. """
    run_every = timedelta(seconds=30)
    def run(self, capture_length=30, *args, **kwargs):
        iostats = zfs.pool.iostat(capture_length=capture_length)
        timestamp_end = timezone.now()

        for i in iostats:
            try:
                pool = Pool.objects.get(name=i)
            except (KeyError, Pool.DoesNotExist):
                logger.error('Got data for an unknown pool "%s"', i)
                continue

            del iostats[i]['name']

            for j in iostats[i].keys():
                if j not in ['timestamp']:
                    statsd.gauge('iostats.%s.%s' % (pool.name, j), iostats[i][j])

            iostats[i]['timestamp_end'] = timestamp_end

            for j in ['alloc', 'free', 'bandwidth_read', 'bandwidth_write']:
                # Convert human readable to bytes
                iostats[i][j] = int(convert_human_to_bytes(iostats[i][j]))

            pool.pool_iostat_set.create(**iostats[i])


class Pool_IOStat_Clean(PeriodicTask):
    """ Periodic Task to clean old IOStats per pool in db """
    run_every = timedelta(days=1)
    def run(self, *args, **kwargs):
        age_threshold = timedelta(days=180)
        count = Pool_IOStat.objects.all().count()

        try:
            count_to_remove = Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - age_threshold).count()
        except (KeyError, Pool_IOStat.DoesNotExist):
            raise Exception("Cannot get list of entries to remove")

        if count_to_remove > 0:
            Pool_IOStat.objects.filter(timestamp_end__lt=timezone.now() - age_threshold).delete()

            logger.debug("Deleted %d/%d entires", count_to_remove, count)


"""
KStats
"""

class KStats_Update(PeriodicTask):
    run_every = timedelta(minutes=1)
    def run(self, *args, **kwargs):
        ks = kstats.get_tree()
        for key in ks.keys():
            self.kstats_walk(key, ks[key])

    def kstats_walk(self, name, value):
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)

        if isinstance(value, basestring):
            #logger.debug('Got basestring %s: %s', name, value)
            #print 'Got basestring %s: %s' % (name, value)
            statsd.gauge(name, value)

        elif isinstance(value, list):
            for x,v in enumerate(value):
                self.kstats_walk('%s.%s' % (name, x), v)

        elif isinstance(value, dict):
            #logger.debug('Got dict %s: %s', name, value)
            if 'value' in value:
                self.kstats_walk(name, value['value'])
            else:
                for k,v in value.iteritems():
                    if k in ['flags']: continue
                    self.kstats_walk('%s.%s' % (name, k), v)

        else:
            logger.error('Got unknown KStat type: %s: %s', name, value)



"""
RRD Stats
"""

#@periodic_task(run_every=timedelta(minutes=5))
def rrd_update(*args, **kwargs):
    StartTime = int(time.time())
    ks = kstats().kstat

    ksMap = {'zfs': {
                    'zfetchstats': {},
                    'xuio_stats': {},
                    'dmu_tx': {
                            'GAUGE': {
                                    'dmu_tx': ['dmu_tx_assigned', 'dmu_tx_delay', 'dmu_tx_error', 'dmu_tx_suspended', 'dmu_tx_group',
                                               'dmu_tx_how', 'dmu_tx_dirty_throttle', 'dmu_tx_write_limit', 'dmu_tx_quota'],
                            },
                            'DERIVE': {
                                    'dmu_tx_memory': ['dmu_tx_memory_reserve', 'dmu_tx_memory_reclaim', 'dmu_tx_memory_inflight'],
                            },
                    },
                    'vdev_cache_stats': {},
                    'fm': {},
                    'arcstats': {
                        'GAUGE': {
                            'cache_size': ['size', 'l2_size'],
                                'arc_hitmiss': ['hits', 'misses'],
                                'l2_hitmiss': ['l2_hits', 'l2_misses'],
                            },
                            'DERIVE': {
                                #'cache_operation': ['allocated', 'deleted', 'stolen'],
                                'mutex_operation': ['mutex_miss'],
                                'hash_collisions': ['hash_collisions'],
                                'cache_eviction': ['evict_l2_cached', 'evict_l2_eligible', 'evict_l2_ineligible'],
                                'cache_result': ['demand_data_hits', 'demand_metadata_hits', 'prefetch_data_hits', 'prefetch_metadata_hits',
                                                 'demand_data_misses', 'demand_metadata_misses', 'prefetch_data_misses',
                                                 'prefetch_metadata_misses'],
                            },
                    }}}

    RRDs = {}
    for rmodule in ksMap.keys():
        for kmodule in ksMap[rmodule].keys():
            for dsType in ksMap[rmodule][kmodule].keys():
                for filename in ksMap[rmodule][kmodule][dsType].keys():
                    rrd_path = os.path.join(settings.DATA_DIR, "rrd", filename + ".rrd")

                    DSs = []
                    Values = []
                    RRAs = []

                    GItems = []

                    for i, kstat_raw in enumerate(ksMap[rmodule][kmodule][dsType][filename]):
                        s_kstat = kstat_raw.split('_')
                        for x, y in enumerate(filename.split('_')):
                            #logger.debug("x=%s y=%s %s", s_kstat[0], y, x)

                            if (len(s_kstat) == 1) or (s_kstat[0] != y):
                                break
                            s_kstat = s_kstat[1:]

                        for x, y in enumerate(s_kstat):
                            kstat = '_'.join(s_kstat)
                            if len(kstat) < 16:
                                break
                            s_kstat[x] = s_kstat[x][:1]

                        kstat_pretty = kstat.replace('_', ' ').capitalize()
                        #logger.debug("dstype=%s, filename=%s, kstat_raw=%s, kstat=%s, kstat_pretty=%s, value=%s",
                        #              dsType, filename, kstat_raw, kstat, kstat_pretty,
                        #              ks[rmodule][kmodule][kstat_raw])

                        ds1 = DataSource(dsName='%s' % kstat, dsType=dsType, heartbeat=300)

                        ds1_def = DEF(rrdfile=rrd_path, vname='%s_n' % kstat, dsName=ds1.name)
                        ds1_area = AREA(defObj=ds1_def,
                                           color='#00C000', legend='%s' % kstat_pretty)

                        ds1avg_vdef = VDEF(vname='%savg' % kstat, rpn='%s,AVERAGE' % ds1_def.vname)
                        ds1avg_line = LINE(defObj=ds1avg_vdef,
                                           color='#0000FF', legend='%s (avg)' % kstat_pretty, stack=True)

                        DSs.append(ds1)
                        Values.append(ks[rmodule][kmodule][kstat_raw])

                        for i in ds1_def, ds1_area, ds1avg_vdef, ds1avg_line:
                            GItems.append(i)

                    for (x, y) in ([1, 600], [6, 700], [24, 775], [288, 797]):
                        RRAs.append(RRA(cf='AVERAGE', xff=0.5, steps=x, rows=y))

                    rrd = RRD(rrd_path, ds=DSs, rra=RRAs, start=920804400, backend=bindings)

                    rrd.bufferValue(StartTime, *Values)

                    if not os.path.isfile(rrd_path):
                        rrd.create()
                    else:
                        rrd.update()

                    ##
                    ## Graph
                    ##

                    # Let's configure some custom colors for the graph
                    #ca = ColorAttributes()
                    #ca.back = '#333333'
                    #ca.canvas = '#333333'
                    #ca.shadea = '#000000'
                    #ca.shadeb = '#111111'
                    #ca.mgrid = '#CCCCCC'
                    #ca.axis = '#FFFFFF'
                    #ca.frame = '#AAAAAA'
                    #ca.font = '#FFFFFF'
                    #ca.arrow = '#FFFFFF'

##
## Image creation code
##
#                    endTime = int(round(time.time()))
#                    delta = timedelta(hours=1)
#                    startTime = int(endTime - delta.seconds)
#                    step = 300
#                    #maxSteps = int((endTime - startTime) / step)
#
#                    # Now that we've got everything set up, let's make a graph
#                    g = Graph(rrd_path + '-last_hour.png',
#                              start=int(startTime), end=int(endTime),
#                              vertical_label='%s' % filename.replace('_', ' ').capitalize(),
#                              backend=bindings)
#                    #color=ca, backend=bindings)
#
#                    #VDEF:ds0max=ds0,MAXIMUM
#                    #VDEF:ds0avg=ds0,AVERAGE
#                    #VDEF:ds0min=ds0,MINIMUM
#                    #VDEF:ds0pct=ds0,95,PERCENT
#                    #VDEF:ds1max=ds1,MAXIMUM
#                    #VDEF:ds1avg=ds1,AVERAGE
#                    #VDEF:ds1min=ds1,MINIMUM
#                    #VDEF:ds1pct=ds1,95,PERCENT
#
#                    g.data.extend(GItems)
#
#                    g.write()

                    #g.filename = graphfileLg
                    #g.width = 800
                    #g.height = 400
                    #g.write()

                    ## Let's set up the objects that will be added to the graph
                    #def1 = DEF(rrdfile=myRRD.filename, vname='in', dsName=ds1.name)
                    #def2 = DEF(rrdfile=myRRD.filename, vname='out', dsName=ds2.name)
                    ## Here we're just going to mulitply the in bits by 100, solely for
                    ## the purpose of display
                    #cdef1 = CDEF(vname='hundredin', rpn='%s,%s,*' % (def1.vname, 100))
                    #cdef2 = CDEF(vname='negout', rpn='%s,-1,*' % def2.vname)
                    #area1 = AREA(defObj=cdef1, color='#FFA902', legend='Bits In')
                    #area2 = AREA(defObj=cdef2, color='#A32001', legend='Bits Out')

                    ## Let's configure some custom colors for the graph
                    #ca = ColorAttributes()
                    #ca.back = '#333333'
                    #ca.canvas = '#333333'
                    #ca.shadea = '#000000'
                    #ca.shadeb = '#111111'
                    #ca.mgrid = '#CCCCCC'
                    #ca.axis = '#FFFFFF'
                    #ca.frame = '#AAAAAA'
                    #ca.font = '#FFFFFF'
                    #ca.arrow = '#FFFFFF'

                    ## Now that we've got everything set up, let's make a graph
                    #g = Graph('dummy.png', end=endTime, vertical_label='Bits', 
                        #color=ca)
                    #g.data.extend([def1, def2, cdef1, cdef2, area2, area1])
                    #g.title = '"In- and Out-bound Traffic Across Local Router"'
                    ##g.logarithmic = ' '

                    ## Iterate through the different resoltions for which we want to 
                    ## generate graphs.
                    #for time, step in times:
                        ## First, the small graph
                        #g.filename = graphfile % (exampleNum, time)
                        #g.width = 400
                        #g.height = 100
                        #g.start=endTime - time
                        #g.step = step
                        #g.write(debug=False)

                        ## Then the big one
                        #g.filename = graphfileLg % (exampleNum, time)
                        #g.width = 800
                        #g.height = 400
                        #g.write()



                    RRDs[filename] = rrd




#def temp_graphs_rrd_update(*args, **kwargs):
        #graphs = {'arcstats': {
                ## time
                #fields: ['mtxmis','arcsz','mrug','l2hit%','mh%','l2miss%','read','c','mfug','miss','dm%','dhit','pread','dread','pmis','l2miss','l2bytes','pm%','mm%','hits','mfu','l2read','mmis','rmis','mhit','mru','ph%','eskip','l2size','l2hits','hit%','miss%','dh%','mread','phit'],
        #}, '<pool>_iostats': {
                #fields: ['pool', 'alloc', 'free', 'bandwidth_read', 'bandwidth_write', 'iops_read', 'iops_write'],
        #}, '<dataset>_properties': {
                #fields: ['available', 'compressratio', 'refcompressratio', 'referenced', 'used', 'usedbychildren', 'usedbydataset', 'usedbyrefreservation',
                         #'usedbysnapshots', 'userrefs', 'copies', 'quota', 'recordsize', 'refquota', 'refreservation', 'reservation', 'volsize'],
        #}}


#def pool_utilization():
#   graph = {}

#   for p in Pool.objects.all():
#       #iostats = p.pool_iostat_set.order_by('timestamp')[:count:offset]
#       iostats = p.pool_iostat_set.order_by('-timestamp')[:count]

#       graph[p.name] = {}

#       total = int(iostats[0].alloc + iostats[0].free)
#       graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

#   return graph


#def graph_stats(count=1):
#    """ Gets graph stats """
#    graph = {}

#    for p in Pool.objects.all():
#        iostats = p.pool_iostat_set.order_by('-timestamp')[:count]
#        #iostats = p.pool_iostat_set.order_by('-timestamp')[:count]

#        graph[p.name] = {}

#        total = int(iostats[0].alloc + iostats[0].free)
#        graph[p.name]['graph_utilization'] = {'values': [float(iostats[0].alloc / float(total) * 100), float(iostats[0].free / float(total) * 100)] }

#        graph[p.name]['graph_iops'] = {'values': [[], []]}
#        graph[p.name]['graph_throughput'] = {'values': [[], []]}
#        for iostat in iostats:
#            graph[p.name]['graph_iops']['values'][0].insert(0, int(iostat.iops_read))
#            graph[p.name]['graph_iops']['values'][1].insert(0, int(iostat.iops_write))
#            graph[p.name]['graph_throughput']['values'][0].insert(0, int(iostat.bandwidth_read))
#            graph[p.name]['graph_throughput']['values'][1].insert(0, int(iostat.bandwidth_write))
#    return graph


