import time
import os, logging, time
import os, logging
import re

from celery.task import periodic_task
from datetime import timedelta
from kstats import kstats
from pyrrd.backend import bindings
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, ColorAttributes, Graph
from pyrrd.rrd import DataSource, RRA, RRD

@periodic_task(run_every=timedelta(minutes=5))
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
                    rrd_path = "rrd/" + filename + ".rrd"

                    DSs = []
                    Values = []
                    RRAs = []

                    GItems = []

                    for i, kstat_raw in enumerate(ksMap[rmodule][kmodule][dsType][filename]):
                        s_kstat = kstat_raw.split('_')
                        for x, y in enumerate(filename.split('_')):
                            #logging.debug("x=%s y=%s %s", s_kstat[0], y, x)

                            if (len(s_kstat) == 1) or (s_kstat[0] != y):
                              break
                            s_kstat = s_kstat[1:]

                        for x, y in enumerate(s_kstat):
                            kstat = '_'.join(s_kstat)
                            if len(kstat) < 16:
                                break
                            s_kstat[x] = s_kstat[x][:1]

                        kstat_pretty = kstat.replace('_', ' ').capitalize()
                        logging.debug("dstype=%s, filename=%s, kstat_raw=%s, kstat=%s, kstat_pretty=%s, value=%s",
                                      dsType, filename, kstat_raw, kstat, kstat_pretty,
                                      ks[rmodule][kmodule][kstat_raw])

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

                    endTime = int(round(time.time()))
                    delta = timedelta(hours=1)
                    startTime = int(endTime - delta.seconds)
                    step = 300
                    maxSteps = int((endTime - startTime) / step)

                    # Now that we've got everything set up, let's make a graph
                    g = Graph(rrd_path + '-last_hour.png',
                              start=int(startTime), end=int(endTime),
                              vertical_label='%s' % filename.replace('_', ' ').capitalize(),
                              backend=bindings)
                    #color=ca, backend=bindings)

#    VDEF:ds0max=ds0,MAXIMUM
    #VDEF:ds0avg=ds0,AVERAGE
    #VDEF:ds0min=ds0,MINIMUM
    #VDEF:ds0pct=ds0,95,PERCENT
    #VDEF:ds1max=ds1,MAXIMUM
    #VDEF:ds1avg=ds1,AVERAGE
    #VDEF:ds1min=ds1,MINIMUM
    #VDEF:ds1pct=ds1,95,PERCENT

                    g.data.extend(GItems)

                    g.write()

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



