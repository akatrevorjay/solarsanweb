from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core import serializers

from utils import qdct_as_kwargs, dict_diff
from response import JSONResponse
from django.views.decorators.csrf import csrf_exempt

from solarsan.utils import *
from solarsan.models import *

import time
import re

import os
import sys
import logging

# RRD Graphs
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT, ColorAttributes, Graph

class rarrd:
    def __init__(self, *args, **kwargs):
            self.data = kwargs

            if not self.data.has_key('dss'):
                self.data['dss'] = []
                self.data['dss'].append( DataSource(dsName=self.data.get('dsName', self.data['name'][:16]),
                                       dsType=self.data.get('dsType', 'COUNTER'),
                                       heartbeat=self.data.get('heartbeat', 300) ) )

            if not self.data.has_key('rras'):
                self.data['rras'] = []
                self.data['rras'].append(RRA(cf='AVERAGE', xff=0.5, steps=1, rows=600))
                self.data['rras'].append(RRA(cf='AVERAGE', xff=0.5, steps=6, rows=700))
                self.data['rras'].append(RRA(cf='AVERAGE', xff=0.5, steps=24, rows=775))
                self.data['rras'].append(RRA(cf='AVERAGE', xff=0.5, steps=288, rows=797))
                #self.data['rras'].append(RRA(cf='MAX', xff=0.5, steps=1, rows=600))
                #self.data['rras'].append(RRA(cf='MAX', xff=0.5, steps=6, rows=700))
                #self.data['rras'].append(RRA(cf='MAX', xff=0.5, steps=24, rows=775))
                #self.data['rras'].append(RRA(cf='MAX', xff=0.5, steps=288, rows=797))

            self.data['filename'] = self.data.get('filename', "rrd/"+self.data['name']+".rrd")

            self.data['rrd'] = RRD(self.data['filename'],
                        ds=self.data['dss'], rra=self.data['rras'], start=self.data.get('start', 920804400))
    def create_or_update(self, *args, **kwargs):
        if not os.path.isfile(self.data['filename']):
            return self.data['rrd'].create()
        else:
            return self.data['rrd'].update()
    def bufval(self, *args, **kwargs):
            return self.data['rrd'].bufferValue(kwargs.get('time', int(time.time())), *args)

def rrd_update(*args, **kwargs):
    k = Kstat()
    k.get_kstat()
    ks = k.kstat

    ## arcstats
    arcstats = ks['zfs']['arcstats']

    rrds = {'zfs': {
                    'zfetchstats': {},
                    'xuio_stats': {},
                    'dmu_tx': {},
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
                                'cache_result': ['demand_data_hits', 'demand_metadata_hits', 'prefetch_data_hits', 'prefetch_metadata_hits', 'demand_data_misses', 'demand_metadata_misses',
                                                 'prefetch_data_misses', 'prefetch_metadata_misses'],
                            },
                    }}}

    rarrds = {}
    for rmodule in rrds.keys():
            for kmodule in rrds[rmodule].keys():
                    for dsType in rrds[rmodule][kmodule].keys():
                            for filename in rrds[rmodule][kmodule][dsType].keys():
                                    for kstat in rrds[rmodule][kmodule][dsType][filename]:
                                            logging.debug("Arr kstat=" + kstat)
                                            rarrds[kstat] = rarrd(name=kstat, data={'dsType': dsType})
                                            rarrds[kstat].bufval(k.kstat[rmodule][kmodule][kstat])
                                            rarrds[kstat].create_or_update()
    return 0

def rrdgraph(*args, **kwargs):
        # Let's set up the objects that will be added to the graph
        def1 = DEF(rrdfile=myRRD.filename, vname='in', dsName=ds1.name)
        def2 = DEF(rrdfile=myRRD.filename, vname='out', dsName=ds2.name)
        # Here we're just going to mulitply the in bits by 100, solely for
        # the purpose of display
        cdef1 = CDEF(vname='hundredin', rpn='%s,%s,*' % (def1.vname, 100))
        cdef2 = CDEF(vname='negout', rpn='%s,-1,*' % def2.vname)
        area1 = AREA(defObj=cdef1, color='#FFA902', legend='Bits In')
        area2 = AREA(defObj=cdef2, color='#A32001', legend='Bits Out')

        # Let's configure some custom colors for the graph
        ca = ColorAttributes()
        ca.back = '#333333'
        ca.canvas = '#333333'
        ca.shadea = '#000000'
        ca.shadeb = '#111111'
        ca.mgrid = '#CCCCCC'
        ca.axis = '#FFFFFF'
        ca.frame = '#AAAAAA'
        ca.font = '#FFFFFF'
        ca.arrow = '#FFFFFF'

        # Now that we've got everything set up, let's make a graph
        g = Graph('dummy.png', end=endTime, vertical_label='Bits', 
            color=ca)
        g.data.extend([def1, def2, cdef1, cdef2, area2, area1])
        g.title = '"In- and Out-bound Traffic Across Local Router"'
        #g.logarithmic = ' '

        # Iterate through the different resoltions for which we want to 
        # generate graphs.
        for time, step in times:
            # First, the small graph
            g.filename = graphfile % (exampleNum, time)
            g.width = 400
            g.height = 100
            g.start=endTime - time
            g.step = step
            g.write(debug=False)
            
            # Then the big one
            g.filename = graphfileLg % (exampleNum, time)
            g.width = 800
            g.height = 400
            g.write()


def temp_graphs_rrd_update(*args, **kwargs):
        graphs = {'arcstats': {
                # time
                fields: ['mtxmis','arcsz','mrug','l2hit%','mh%','l2miss%','read','c','mfug','miss','dm%','dhit','pread','dread','pmis','l2miss','l2bytes','pm%','mm%','hits','mfu','l2read','mmis','rmis','mhit','mru','ph%','eskip','l2size','l2hits','hit%','miss%','dh%','mread','phit'],
        }, '<pool>_iostats': {
                fields: ['pool', 'alloc', 'free', 'bandwidth_read', 'bandwidth_write', 'iops_read', 'iops_write'],
        }, '<dataset>_properties': {
                fields: ['available', 'compressratio', 'refcompressratio', 'referenced', 'used', 'usedbychildren', 'usedbydataset', 'usedbyrefreservation',
                         'usedbysnapshots', 'userrefs', 'copies', 'quota', 'recordsize', 'refquota', 'refreservation', 'reservation', 'volsize'],
        }}

class Kstat:
    def __init__(self):
        self.data = []
    def get_kstat(self, *args, **kwargs):
        if not hasattr(self, 'kstat'):
            self.kstat = {}
        self.kstat_next = {}
        self.kstat_diff = {}
        kstat_path = "/proc/spl/kstat/"
        try:
            modules = os.listdir(kstat_path)
        except:
            logging.error('Could not get list of kstat modules')

        for i in modules:
            self.kstat_next[i] = {}
            self.kstat_diff[i] = {}
            for j in os.listdir(os.path.join(kstat_path, i)):
                self.kstat_next[i][j] = {}
                for k, line in enumerate(str(open(os.path.join(kstat_path, i, j), 'r').read()).splitlines()):
                    if k < 2:
                        continue
                    l = line.split()
                    self.kstat_next[i][j][ l[0] ] = l[2]
                if self.kstat.has_key(i) and self.kstat_next.has_key(i):
                    if self.kstat[i].has_key(j) and self.kstat_next[i].has_key(j):
                        self.kstat_diff[i][j] = dict_diff(self.kstat[i][j], self.kstat_next[i][j])

        self.kstat_prev = self.kstat
        self.kstat = self.kstat_next
        del self.kstat_next
    def get_kmem(self, *args, **kwargs):
        if not hasattr(self, 'kmem'):
            self.kmem = {}
        self.kmem_next = {}
        self.kmem_diff = {}
        kmem_path = "/proc/spl/kmem/"
        try:
            modules = os.listdir(kmem_path)
        except:
            logging.error('Could not get list of kmem modules')

        for i in modules:
            self.kmem_next[i] = {}
            self.kmem_diff[i] = {}
            for j, line in enumerate(str(open(os.path.join(kmem_path, i), 'r').read()).splitlines()):
                if j < 2:
                    continue
                l = line.split()
                self.kmem_next[i][ l[0] ] = l[1:]
                if self.kmem.has_key(i) and self.kmem_next.has_key(i):
                    self.kmem_diff[i] = dict_diff(self.kmem[i], self.kmem_next[i])

        self.kmem_prev = self.kmem
        self.kmem = self.kmem_next
        del self.kmem_next


