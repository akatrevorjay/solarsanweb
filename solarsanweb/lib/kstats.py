"""
$ kstats.py -- Port of arcstat.pl from perl to python, with a (what I believe) is a better interface.
~ Trevor Joynson aka trevorj <trevorj@localhostsolutions.com>
"""

import string
from copy import copy
import os, logging
from solarsan.utils import dict_diff
import collections


#a = [3,4,5,5,5,6]
#b = [1,3,4,4,5,5,6,7]
#a_multiset = collections.Counter(a)
#b_multiset = collections.Counter(b)
#overlap = list((a_multiset & b_multiset).elements())
#a_remainder = list((a_multiset - b_multiset).elements())
#b_remainder = list((b_multiset - a_multiset).elements())
#print overlap, a_remainder, b_remainder


KSTATS_PATH = "/proc/spl"


def get_tree():
    kstats_path = KSTATS_PATH
    if kstats_path.endswith(os.path.sep):
        kstats_path = kstats_path[:-1]

    ret = {}
    for root, dirs, files in os.walk(kstats_path):
        for file in files:
            file_path = os.path.join(root, file)

            path = file_path[len(kstats_path):].translate(string.maketrans('/_', '  ')).split()
            cur_file = ret
            for p in path:
                if not p in cur_file: cur_file[p] = {}
                cur_file = cur_file[p]

            m_path = collections.Counter(path)

            for x, line in enumerate(str(open(os.path.join(root, file), 'r').read()).splitlines()):
                if x == 1:
                    header = line.split()
                    if 'data' in header and 'value' not in header:
                        header[header.index('data')] = 'value'
                if x < 2 or not header: continue

                stat = dict(zip(header, line.split(None, len(header))))

                name = stat['name'].replace('_', ' ').split()
                del stat['name']

                m_name = collections.Counter(name)
                #fixed_name = list((m_path - m_name).elements()) + list((m_path & m_name).elements()) + list((m_name - m_path).elements())
                fixed_name = list((m_name - m_path).elements())
                fixed_name = ['_'.join(fixed_name)]

                cur = cur_file
                for p in fixed_name[:-1]:
                    if not p in cur: cur[p] = {}
                    cur = cur[p]

                cur[fixed_name[-1]] = stat

    ## TODO Count each dict element; if there's only a single element in a tree level, then flatten it into an underscore
    ## Maybe we just don't make it a tree till the end here instead and expand it upon underscores if there's more than one value with an underscored phrase?

    #def kstats_walk(name, value):
    #    if isinstance(value, int) or isinstance(value, float):
    #        value = str(value)

    #    if isinstance(value, basestring):
    #        #logger.debug('Got basestring %s: %s', name, value)
    #        statsd.gauge(name, value)

    #    elif isinstance(value, list):
    #        for x,v in enumerate(value):
    #            kstats_walk('%s.%s' % (name, x), v)

    #    elif isinstance(value, dict):
    #        #logger.debug('Got dict %s: %s', name, value)
    #        if 'value' in value:
    #            kstats_walk(name, value['value'])
    #        else:
    #            for k,v in value.iteritems():
    #                kstats_walk('%s.%s' % (name, k), v)

    #    #else:
    #    #    logger.debug('Got unknown stat %s: %s', name, value)


    return ret


def get():
    kstats_path = KSTATS_PATH
    if kstats_path.endswith(os.path.sep):
        kstats_path = kstats_path[:-1]

    ret = {}
    for root, dirs, files in os.walk(kstats_path):
        for file in files:
            file_path = os.path.join(root, file)

            path = file_path[len(kstats_path):].translate(string.maketrans('/_', '  ')).split()
            cur_file = ret
            for p in path[:1]:
                if not p in cur_file: cur_file[p] = {}
                cur_file = cur_file[p]

            rpath = copy(path)
            rpath.reverse()

            for x, line in enumerate(str(open(os.path.join(root, file), 'r').read()).splitlines()):
                if x == 1:
                    header = line.split()
                    if 'data' in header:
                        header[header.index('data')] = 'value'
                if x < 2 or not header: continue

                stat = dict(zip(header, line.split(None, len(header))))
                if not 'value' in header:
                    logging.debug('Leaving behind kstat %s because it has no value', stat)
                    continue
                name = stat['name'].replace('_', ' ').split()

                for p,n in zip(rpath, name):
                    if p == n: name.pop(0)
                    else: break

                del stat['name']
                cur_file['.'.join(path[1:] + name)] = stat['value']
    return ret


class KStats:
    def __init__(self):
        self.update()
    def update(self, *args, **kwargs):
        self.get_kstat()
        self.get_kmem()
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


