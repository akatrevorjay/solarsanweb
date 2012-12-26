
#import zmq
import threading
import time

from . import discovery


class Thread(threading.Thread):
    def __init__(self, func):
        self.func = func
        threading.Thread.__init__(self)

    def run(self):
        self.func()


def main():
    threads = []
    for m in [discovery]:
        t = Thread(m.main)
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1000)
    except (KeyboardInterrupt, SystemExit):
        raise
