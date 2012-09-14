
import sys
import subprocess
import random
import time
import threading
import Queue

class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue, bufsize=-1):
        assert isinstance(queue, Queue.Queue)
        #if bufsize == -1:
        assert callable(fd.readline)
        #else:
        #    assert callable(fd.read)
        threading.Thread.__init__(self)
        self.bufsize = bufsize
        self._fd = fd
        self._queue = queue

    def run(self):
        '''Read some data onto the queue'''
        # Line buffering = bufsize == -1
        if self.bufsize == -1:
            for line in iter(self._fd.readline, ''):
                self._queue.put(line)
        #else:
        #    while self._fd:
        #        self._fd.read
        #        self._queue.put(buf)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()

def consume(command):
    '''
    Example of how to consume standard output and standard error of
    a subprocess asynchronously without risk on deadlocking.
    '''

    # Launch the command as subprocess.
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Launch the asynchronous readers of the process' stdout and stderr.
    stdout_queue = Queue.Queue()
    stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
    stdout_reader.start()
    stderr_queue = Queue.Queue()
    stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
    stderr_reader.start()

    # Check the queues if we received some output (until there is nothing more to get).
    while not stdout_reader.eof() or not stderr_reader.eof():
        # Show what we received from standard output.
        while not stdout_queue.empty():
            line = stdout_queue.get()
            print 'Received line on standard output: ' + repr(line)

        # Show what we received from standard error.
        while not stderr_queue.empty():
            line = stderr_queue.get()
            print 'Received line on standard error: ' + repr(line)

        # Sleep a bit before asking the readers again.
        time.sleep(.1)

    # Let's be tidy and join the threads we've started.
    stdout_reader.join()
    stderr_reader.join()

    # Close subprocess' file descriptors.
    process.stdout.close()
    process.stderr.close()

def produce(items=10):
    '''
    Dummy function to randomly render a couple of lines
    on standard output and standard error.
    '''
    for i in range(items):
        output = random.choice([sys.stdout, sys.stderr])
        output.write('Line %d on %s\n' % (i, output))
        output.flush()
        time.sleep(random.uniform(.1, 1))

def asyncsubproc():
    # The main flow:
    # if there is an command line argument 'produce', act as a producer
    # otherwise be a consumer (which launches a producer as subprocess).
    if len(sys.argv) == 2 and sys.argv[1] == 'produce':
        produce(10)
    else:
        consume(['python', sys.argv[0], 'produce'])

