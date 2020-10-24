from multiprocessing import Queue
from containers import TransferPackage


class IPC:
    def __init__(self):
        self.queues = {}

    def create_queues(self, *entities):
        for e in entities:
            self.queues[e] = Queue()

    @staticmethod
    def pack(**kwargs):
        t = TransferPackage()
        t.pack(**kwargs)
        return t

    def send(self, *, dst, package, **kwargs):
        package.label(**kwargs)
        self.queues[dst].put(package)

    def check_queue(self, entity):
        queue: Queue = self.queues[entity]
        if not queue.empty():
            return queue.get()
        return None
