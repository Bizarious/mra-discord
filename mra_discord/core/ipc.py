from typing import Optional
from multiprocessing import Queue, Pipe
from multiprocessing.connection import Connection
from .errors import (IPCQueueAlreadyExists,
                     IPCQueueDoesNotExist
                     )


class IPCPackage:
    """
    Offers a unified package interface in ipc communication.
    """

    def __init__(self):
        self._content = {}
        self._labels = {}

    def label(self, *,  command, **labels):
        self._labels["command"] = command
        for key, value in labels.items():
            self._labels[key] = value

    def pack(self, **content):
        for key, value in content.items():
            self._content[key] = value

    @property
    def labels(self):
        return self._labels

    @property
    def content(self):
        return self._content


class IPCConnection:

    def __init__(self, pipe: Connection):
        self._pipe = pipe


class IPC:
    """
    Handles ipc communication between different modules.
    """

    def __init__(self):
        # holds all queues mapped to the module name
        self._queues: dict[str: Queue] = {}

    def add_queue(self, name: str) -> None:
        if name in self._queues:
            raise IPCQueueAlreadyExists(f'There is already a queue for "{name}"')
        self._queues[name] = Queue()

    def remove_queue(self, name: str) -> None:
        if name not in self._queues:
            raise IPCQueueDoesNotExist(f'There is no queue for "{name}"')
        del self._queues[name]

    def establish_connection(self, target: str) -> IPCConnection:
        if target not in self._queues:
            raise IPCQueueDoesNotExist(f'Cannot establish connection: target "{target}" is not registered')

        connection1, connection2 = Pipe()
        package = IPCPackage()
        package.label(command="establish")
        package.pack(pipe=connection2)

        self._queues[target].put(package)

        return IPCConnection(connection1)

    def pull(self, target: str, block: Optional[bool] = True, timeout: Optional[float] = None) -> IPCPackage:
        queue: Queue = self._queues[target]
        return queue.get(block=block, timeout=timeout)

    def broadcast(self, package: IPCPackage):
        pass

    def send_manually(self, target: str, package: IPCPackage):
        pass
