from multiprocessing import Queue
from core.containers import TransferPackage
from multiprocessing import Pipe
from typing import Union, Any


class IPC:
    def __init__(self):
        self.queues = {}

    def create_queues(self, *entities: str):
        for e in entities:
            self.queues[e] = Queue()

    @staticmethod
    def pack(**kwargs):
        t = TransferPackage()
        t.pack(**kwargs)
        return t

    def send(self, *, dst: str, create_pipe=False, package, **kwargs):
        if create_pipe:
            pipe1, pipe2 = Pipe()
        else:
            pipe1, pipe2 = None, None
        package.label(pipe=pipe2, **kwargs)
        self.queues[dst].put(package)
        return pipe1

    def check_queue(self, entity: str) -> Union[Any, None]:
        queue: Queue = self.queues[entity]
        if not queue.empty():
            return queue.get()
        return None

    def check_queue_block(self, entity: str) -> Union[Any, None]:
        queue: Queue = self.queues[entity]
        return queue.get()
