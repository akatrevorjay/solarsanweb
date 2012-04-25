import os, logging
from solarsan.utils import dict_diff

class kstats:
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


