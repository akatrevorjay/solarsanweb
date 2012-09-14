

from transports.pylibssh2 import SSHRemoteClientNonBlocking
from subprocess import CalledProcessError
from backup.backup_zfs import Dataset, Pool, PoolSet, Snapshot

import sys
import os
import threading
import subprocess



def children_first(pathlist):
    return sorted(pathlist, key=lambda x: -x.count('/'))


def parents_first(pathlist):
    return sorted(pathlist, key=lambda x: x.count('/'))


chronosorted = sorted




def run_command(cmd, inp=None, capture_stderr=False):
    if capture_stderr:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    else:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)

    # work around the stupidest python bug
    stdout = []
    stderr = []

    def read(pipe, chunk_accumulator):
        while True:
            chunk = pipe.read()
            if chunk == '':
                break
            chunk_accumulator.append(chunk)

    soreader = threading.Thread(target=read, args=(p.stdout, stdout))
    soreader.setDaemon(True)
    soreader.start()
    if capture_stderr:
        sereader = threading.Thread(target=read, args=(p.stderr, stderr))
        sereader.setDaemon(True)
        sereader.start()

    if inp:
        p.stdin.write(inp)

    exit = p.wait()
    soreader.join()
    if capture_stderr:
        sereader.join()
    if exit != 0:
        c = CalledProcessError(exit, cmd)
        raise c
    return (''.join(stdout), ''.join(stderr))




def simplify(x):
    '''Take a list of tuples where each tuple is in form [v1,v2,...vn]
    and then coalesce all tuples tx and ty where tx[v1] equals ty[v2],
    preserving v3...vn of tx and discarding v3...vn of ty.

    m = [
    (1,2,"one"),
    (2,3,"two"),
    (3,4,"three"),
    (8,9,"three"),
    (4,5,"four"),
    (6,8,"blah"),
    ]
    simplify(x) -> [[1, 5, 'one'], [6, 9, 'blah']]
    '''

    y = list(x)
    if len(x) < 2:
        return y
    for (idx, o) in enumerate(list(y)):
        for (idx2, p) in enumerate(list(y)):
            if idx == idx2:
                continue
            if o and p and o[0] == p[1]:
                y[idx] = None
                y[idx2] = list(p)
                y[idx2][0] = p[0]
                y[idx2][1] = o[1]
    return [n for n in y if n is not None]


def uniq(seq, idfun=None):
    '''Makes a sequence 'unique' in the style of UNIX command uniq'''

   # order preserving

    if idfun is None:

        def idfun(x):
            return x

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)

       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:

        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result





def progressbar(pipe, bufsize=-1, ratelimit=-1):

    def clpbar(cmdname):
        barargs = []
        if bufsize != -1:
            barargs = ['-bs', str(bufsize)]
        if ratelimit != -1:
            barargs = barargs + ['-th', str(ratelimit)]
        barprg = subprocess.Popen([cmdname, '-dan'] + barargs,
                                  stdin=pipe, stdout=subprocess.PIPE,
                                  bufsize=bufsize)
        return barprg

    def pv(cmdname):
        barargs = []
        if bufsize != -1:
            barargs = ['-B', str(bufsize)]
        if ratelimit != -1:
            barargs = barargs + ['-L', str(ratelimit)]
        barprg = subprocess.Popen([cmdname, '-ptrb'] + barargs,
                                  stdin=pipe, stdout=subprocess.PIPE,
                                  bufsize=bufsize)
        return barprg

    barprograms = [('bar', clpbar), ('clpbar', clpbar), ('pv', pv)]

    for (name, func) in barprograms:
        try:
            subprocess.call([name, '-h'], stdout=file(os.devnull, 'w'),
                            stderr=file(os.devnull, 'w'),
                            stdin=file(os.devnull, 'r'))
        except OSError, e:
            if e.errno == 2:
                continue
            assert 0, 'not reached while searching for clpbar or pv'
        return func(name)
    raise OSError(2,
                  'no such file or directory searching for clpbar or pv'
                  )





# it is time to determine which datasets need to be synced
# we walk the entire dataset structure, and sync snapshots recursively

def recursive_replicate(s, d):
    sched = []

    # we first collect all snapshot names, to later see if they are on both sides, one side, or what

    all_snapshots = []
    if s:
        all_snapshots.extend(s.get_snapshots())
    if d:
        all_snapshots.extend(d.get_snapshots())
    all_snapshots = [y[1] for y in chronosorted([(x.get_creation(),
                     x.name) for x in all_snapshots])]
    snapshot_pairs = []
    for snap in all_snapshots:
        try:
            ssnap = s.get_snapshot(snap)
        except (KeyError, AttributeError):
            ssnap = None
        try:
            dsnap = d.get_snapshot(snap)
        except (KeyError, AttributeError):
            dsnap = None

        # if the source snapshot exists and is not already in the table of snapshots
        # then pair it up with its destination snapshot (if it exists) or None
        # and add it to the table of snapshots

        if ssnap and not snap in [x[0].name for x in snapshot_pairs]:
            snapshot_pairs.append((ssnap, dsnap))

    # now we have a list of all snapshots, paired up by name, and in chronological order
    # (it's quadratic complexity, but who cares)
    # now we need to find the snapshot pair that happens to be the the most recent common pair

    found_common_pair = False
    for (idx, (m, n)) in enumerate(snapshot_pairs):
        if m and n and m.name == n.name:
            found_common_pair = idx

    # we have combed through the snapshot pairs
    # time to check what the latest common pair is

    if not s.get_snapshots():

        # well, no snapshots in source, do nothing

        pass
    elif found_common_pair is False:

        # no snapshot is in common, problem!
        # theoretically destroying destination dataset and resyncing it recursively would work
        # but this requires work in the optimizer that comes later

        sched.append(('full', s, d, None, snapshot_pairs[-1][0]))
    elif found_common_pair == len(snapshot_pairs) - 1:

        # the latest snapshot of both datasets that is common to both, is the latest snapshot in the source
        # we have nothing to do here because the datasets are "in sync"

        pass
    else:

        # the source dataset has more recent snapshots, not present in the destination dataset
        # we need to transfer those

        snapshots_to_transfer = [x[0] for x in
                                 snapshot_pairs[found_common_pair:]]
        for (n, x) in enumerate(snapshots_to_transfer):
            if n == 0:
                continue
            sched.append(('incremental', s, d, snapshots_to_transfer[n
                         - 1], x))

    # now let's apply the same argument to the children

    children_sched = []
    for c in [x for x in s.children if not isinstance(x, Snapshot)]:
        try:
            cd = d.get_child(c.name)
        except (KeyError, AttributeError):
            cd = None
        children_sched.extend(recursive_replicate(c, cd))

    # and return our schedule of operations to the parent

    return sched + children_sched



def optimize(operation_schedule):

    # now let's optimize the operation schedule
    # the optimization is quite basic
    # step 1: if a snapshot is scheduled to be synced, and its parent has the same snapshot to be synced, we skip it
    # step 2: coalesce operations

    # this optimizer removes superfluous operations and consolidates the remaining ones

    # pass 0: (unimplemented)
    # if any incremental transfers are scheduled, but full transfers are scheduled for their parents
    # then drop them
    # this should not happen so far because the recursive_replicate
    # function should never generate that combination of operations

    # pass 1:
    # group operations based on the source and destination snapshot names
    # look up each operation in its corresponding group
    # if the parent dataset is listed in the corresponding group
    # drop it like a mad beat

    def pass1(sched):

        # first step is to build a dictionary of operations
        # grouped by source snapshot name and destination snapshot name

        operations_by_srcsnap_to_dstsnap = {}
        operations_by_dstsnap = {}
        for (op, src, dst, srcs, dsts) in filter(lambda x: x[0] \
                == 'incremental', sched):
            srcname = src.get_path()
            opsummary = srcs.name + '->' + dsts.name
            if opsummary not in operations_by_srcsnap_to_dstsnap:
                operations_by_srcsnap_to_dstsnap[opsummary] = []
            operations_by_srcsnap_to_dstsnap[opsummary].append((op,
                    src, dst, srcs, dsts))
        for (op, src, dst, srcs, dsts) in sched:
            srcname = src.get_path()
            opsummary = dsts.name
            if opsummary not in operations_by_dstsnap:
                operations_by_dstsnap[opsummary] = []
            operations_by_dstsnap[opsummary].append((op, src, dst,
                    srcs, dsts))

        # second step is to iterate through the operations and look them up in their group

        optimized = []
        for (op, src, dst, srcs, dsts) in sched:
            if op == 'incremental':
                opsummary = srcs.name + '->' + dsts.name
                commonprefix = os.path.commonprefix([x[1].get_path()
                        for x in
                        operations_by_srcsnap_to_dstsnap[opsummary]
                        if x[1].get_path().startswith(src.get_path())
                        or src.get_path().startswith(x[1].get_path())])

                if len(commonprefix) < len(src.get_path()):

                    # the parent is scheduled to experience the same operation as the one evaluated right now

                    continue  # then ignore it and go straight to evaluating the next structure
            elif op == 'full':
                opsummary = dsts.name
                commonprefix = os.path.commonprefix([x[1].get_path()
                        for x in operations_by_dstsnap[opsummary]
                        if x[1].get_path().startswith(src.get_path())
                        or src.get_path().startswith(x[1].get_path())])

                if len(commonprefix) < len(src.get_path()):

                    # the parent is scheduled to send the snapshot that is being evaluated right now

                    continue  # then ignore it and go straight to evaluating the next structure
            else:
                assert 0, 'Not reached'

            # print "Operation",op,src,opsummary,"accepted"

            optimized.append((op, src, dst, srcs, dsts))

        return optimized

    # pass 2:
    # coalesce operations based on contiguousness

    def pass2(sched):

        # first step is to build a dictionary of operations
        # grouped by source dataset

        operations_by_src = {}
        for (op, src, dst, srcs, dsts) in sched:
            if src not in operations_by_src:
                operations_by_src[src] = []
            operations_by_src[src].append((op, src, dst, srcs, dsts))

        # second step is to iterate through it
        # this requires that the operations in sched be sorted

        for (src, operations) in operations_by_src.items():

            # transpose operations so srcs and dsts are the first two

            operations = [(srcs, dsts, op, src, dst) for (op, src, dst,
                          srcs, dsts) in operations]
            operations = simplify(operations)
            operations = [(op, src, dst, srcs, dsts) for (srcs, dsts,
                          op, src, dst) in operations]
            operations_by_src[src] = operations

        # flatten dictionary back into a list, preserving the order of the original schedule

        datasets = uniq([src for (op, src, dst, srcs, dsts) in sched])
        sched = [v for x in datasets for v in operations_by_src[x]]
        return sched

    # pass 3:
    # sort operations so incremental child operations happen before incremental parent operations

    def pass3(sched):
        return sorted(sched, key=lambda k: -k[1].get_path().count('/'))

    operation_schedule = pass1(operation_schedule)
    operation_schedule = pass2(operation_schedule)
    operation_schedule = pass3(operation_schedule)
    return operation_schedule
