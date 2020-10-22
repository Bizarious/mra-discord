from multiprocessing import Queue
from containers import TransferPackage


class IPC:
    def __init__(self):
        self.queues = {}

    def create_queues(self, *entities):
        for e in entities:
            self.queues[e] = Queue()

    def send(self, *, dst, author, channel, **kwargs):
        t = TransferPackage(author_id=author, channel_id=channel, **kwargs)
        self.queues[dst].put(t)

    def put_manually(self, entity, content):
        self.queues[entity].put(content)

    def check_queue(self, entity):
        queue: Queue = self.queues[entity]
        if not queue.empty():
            return queue.get()
        return None
