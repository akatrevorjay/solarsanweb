import os, logging, time
from math import sin, pi

from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, CDEF, VDEF, LINE, AREA, GPRINT, ColorAttributes, Graph
from pyrrd.backend import bindings

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
                               ds=self.data['dss'], rra=self.data['rras'], start=self.data.get('start', 920804400), backend=bindings)
    def create_or_update(self, *args, **kwargs):
        if not os.path.isfile(self.data['filename']):
            return self.data['rrd'].create()
        else:
            return self.data['rrd'].update()
    def bufval(self, *args, **kwargs):
        return self.data['rrd'].bufferValue(kwargs.get('time', int(time.time())), *args)
    def graph(self, *args, **kwargs):
        # Let's set up the objects that will be added to the graph
        i = 0
        dsi = self.data['dss'][i]

        def1 = DEF(rrdfile=self.data['filename'], vname=dsi.name, dsName=dsi.name[:16])
        #def2 = DEF(rrdfile=myRRD.filename, vname='mysilliness', dsName=ds2.name)
        #def3 = DEF(rrdfile=myRRD.filename, vname='myinsanity', dsName=ds3.name)
        #def4 = DEF(rrdfile=myRRD.filename, vname='mydementia', dsName=ds4.name)
        vdef1 = VDEF(vname='myavg', rpn='%s,AVERAGE' % def1.vname)
        area1 = AREA(defObj=def1, color='#FFA902', legend='Raw Data 4')
        #area2 = AREA(defObj=def2, color='#DA7202', legend='Raw Data 3')
        #area3 = AREA(defObj=def3, color='#BD4902', legend='Raw Data 2')
        #area4 = AREA(defObj=def4, color='#A32001', legend='Raw Data 1')
        line1 = LINE(defObj=vdef1, color='#01FF13', legend='Average', stack=True)

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

        day = 24 * 60 * 60
        week = 7 * day
        month = day * 30
        quarter = month * 3
        half = 365 * day / 2
        year = 365 * day

        endTime = int(round(time.time()))
        delta = 13136400
        startTime = int(endTime - delta)
        step = 300
        maxSteps = int((endTime-startTime)/step)

        # Now that we've got everything set up, let's make a graph
        endTime = time.time()
        startTime = endTime - 3 * month
        g = Graph(self.data['filename']+'-last_3m.png', start=int(startTime), end=int(endTime), vertical_label='data', color=ca, backend=bindings)
        g.data.extend([def1, vdef1, area1])
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





