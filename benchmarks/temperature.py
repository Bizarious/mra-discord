from multiprocessing import Process, Queue
from datetime import datetime as dt
import time
import os


class Worker(Process):
    def __init__(self, q):
        Process.__init__(self)
        self.q: Queue = q

    def run(self):
        while True:
            if not self.q.empty():
                break
            if dt.now() == dt.now():
                pass


class Temp(Process):
    def __init__(self, q):
        Process.__init__(self)
        self.q: Queue = q

    def run(self):
        n = 0
        while True:
            n += 1
            if not self.q.empty():
                break
            if n == 5:
                print(os.popen("/opt/vc/bin/vcgencmd measure_temp").read())
                n = 0
            time.sleep(1)


q = Queue()
for _ in range(4):
    w = Worker(q)
    w.start()

t = Temp(q)
t.start()
q.put(input())


