import logging
from typing import Optional, Union
from multiprocessing import Queue, Pipe
from multiprocessing.connection import Connection
from .errors import (IPCQueueAlreadyExists,
                     IPCQueueDoesNotExist,
                     ConnectionTerminated
                     )


class IPCPackage:
    """
    Offers a unified package interface in ipc communication.
    """

    def __init__(self):
        self._content = {}
        self._labels = {}

    def label(self, **labels):
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

    def __init__(self, pipe: Connection, side: str):
        self._pipe = pipe
        self._connection_running = True
        self._side = side

    def send(self, *,
             package: Optional[IPCPackage] = IPCPackage(),
             command: Optional[str] = None,
             status: Optional[str] = None,
             **labels):

        if self._connection_running:
            package.label(command=command, status=status, **labels)
            self._pipe.send(package)
        else:
            raise ConnectionTerminated("The connection has already been terminated")

    def recv(self, timeout: float = 5) -> Union[IPCPackage, None]:
        if not self._pipe.poll(timeout):
            self._connection_running = False
            return None

        try:
            package: IPCPackage = self._pipe.recv()
        except EOFError:
            logging.warning('Received EOFError, most likely due to an unclean termination of the connection. '
                            'Please call "end_communication" on the connection object.')
            return None

        if package.labels["command"] == "end":
            self._connection_running = False
            return None
        return package

    def end_communication(self):
        self.send(command="end")
        self._connection_running = False


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

    def establish_connection(self, target: str, source: str) -> IPCConnection:
        if target not in self._queues:
            raise IPCQueueDoesNotExist(f'Cannot establish connection: target "{target}" is not registered')

        connection1, connection2 = Pipe()
        package = IPCPackage()
        package.label(command="establish")
        package.pack(connection=IPCConnection(connection2, target))

        self._queues[target].put(package)

        return IPCConnection(connection1, source)

    def pull(self, target: str, block: Optional[bool] = True, timeout: Optional[float] = None) -> IPCPackage:
        queue: Queue = self._queues[target]
        return queue.get(block=block, timeout=timeout)

    def send_manually(self, target: str, package: IPCPackage):
        pass
