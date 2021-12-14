from multiprocessing import Queue
from .errors import (IPCQueueAlreadyExistsError,
                     IPCQueueDoesNotExistError
                     )


class IPCPackage:
    pass


class IPC:
    """
    Handles ipc communication between different modules.
    """

    def __init__(self):
        # holds all queues mapped to the module name
        self._queues: dict[str: Queue] = {}

    def add_queue(self, name: str) -> None:
        if name in self._queues:
            raise IPCQueueAlreadyExistsError(f'There is already a queue for "{name}"')
        self._queues[name] = Queue()

    def remove_queue(self, name: str) -> None:
        if name not in self._queues:
            raise IPCQueueDoesNotExistError(f'There is no queue for "{name}"')
        del self._queues[name]

    def send(self):
        pass
