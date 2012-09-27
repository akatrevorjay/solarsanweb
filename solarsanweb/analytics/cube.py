
from django.conf import settings

from pypercube.cube import Cube
from pypercube.expression import EventExpression, MetricExpression, CompoundMetricExpression
from pypercube.expression import Sum, Min, Max, Median, Distinct
from pypercube import time_utils

from datetime import timedelta, datetime
from collections import defaultdict

import logging


class AnalyticsBase(object):
    pass


class CubeAnalytics(AnalyticsBase):
    #def _put(self, **kwargs):
    #    pass

    def _get(self, *args, **kwargs):
        c = Cube(settings.CUBE_HOST)
        stop = kwargs.get('stop', datetime.now())
        start = kwargs.get('start', stop-timedelta(hours=1))
        if not isinstance(start, datetime):
            start = datetime.fromtimestamp(float(start))
        step = kwargs.get('step', None)
        if not step:
            step = time_utils.STEP_5_MIN
        #else:
        #    step = long(step) * 60 * 1000
        metrics = {}
        for f in args:
            m = self._get_metric_expr(f, **kwargs)
            metrics[f] = c.get_metric(m, start=start, stop=stop, step=step)
        return metrics

    def _render(self, *args, **kwargs):
        """ Renders analytics data in specified format """
        metrics = self._get(*args, **kwargs)
        fmt = kwargs.get('format')
        if fmt == 'nvd3':
            #for f in args:
            #    metrics[f] = filter(lambda x: x.value, metrics[f])
            ret = [ {'key': key.replace('_', ' ').title(),
                     'values': map(lambda x: (int(x.time.strftime('%s')) * 1000, x.value or 0),
                                   metrics[key], ),
                     } for key in args ]
        else:
            logging.warn("No such render format '%s'", fmt)
            ret = metrics
        return ret

    def _get_event_expr(self, f, **kwargs):
        return EventExpression(f)

    def _get_metric_expr(self, f, **kwargs):
        e = kwargs.get('event_expr', self._get_event_expr(f, **kwargs))
        return Median(e)

