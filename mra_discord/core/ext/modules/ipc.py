import logging

from multiprocessing import Pipe, Queue
from multiprocessing.connection import Connection
from typing import TYPE_CHECKING, Optional, Any
from threading import Thread

from core.ext import Extension
from core.ext.modules import ExtensionHandlerModule

if TYPE_CHECKING:
    from core.ext.decorators import IPCMessageHandler

LABEL_IPC_SOURCE = "source"

CONTENT_FIELD_AUTHOR = "author"

_COMMAND_ESTABLISH = "establish"
_COMMAND_STOP = "stop"
_COMMAND_END_CONNECTION = "end"

_STATUS_READY = "ready"


class IPCPackage:
    """
    Offers a unified package interface in ipc communication.
    """

    def __init__(self, *, command: Optional[str] = None, status: Optional[str] = None):
        self._content = None
        self._labels = {}
        self._command = command
        self._status = status

    def label(self, key: str, value: Any) -> "IPCPackage":
        self._labels[key] = value
        return self

    def pack(self, content: Any) -> "IPCPackage":
        self._content = content
        return self

    @property
    def labels(self) -> dict:
        return self._labels

    @property
    def content(self) -> Any:
        return self._content

    @property
    def command(self) -> str:
        return self._command

    @property
    def status(self) -> str:
        return self._status


class IPCConnection:

    def __init__(self, pipe: Connection, own_side: str, other_side: str):
        self._pipe = pipe
        self._own_side = own_side
        self._other_side = other_side
        self._logger = logging.getLogger(own_side)
        self._connection_running = True

    def _send(self, package: IPCPackage):

        if not self._connection_running:
            raise ConnectionError("This connection has already been terminated")

        package.label(LABEL_IPC_SOURCE, self._own_side)

        try:
            self._pipe.send(package)
        except (EOFError, ConnectionError) as e:
            self._logger.error(f"Received {e.__class__.__name__} while trying to send a package: {e}")
            self._connection_running = False
            return
        else:
            self._logger.debug("Send package successfully")

    def recv(self, timeout: float = 5.0) -> Optional[IPCPackage]:
        if not self._pipe.poll(timeout):
            self._logger.debug("Reached timeout, terminating connection")
            self.end_communication()
            return None

        try:
            package: IPCPackage = self._pipe.recv()
        except (EOFError, ConnectionError) as e:
            self._logger.error(f"Received {e.__class__.__name__} while trying to receive a package: {e}")
            self._connection_running = False
            return None
        else:
            self._logger.debug("Received package successfully")

        if package.command == _COMMAND_END_CONNECTION:
            self._logger.debug(f"Received connection end signal")
            self._connection_running = False
            return None

        return package

    def send_and_recv(self,
                      package: IPCPackage,
                      *, timeout: float = 5.0,
                      ):

        self._send(package=package)
        return self.recv(timeout)

    def end_communication(self):
        self._send(IPCPackage(command=_COMMAND_END_CONNECTION))
        self._connection_running = False


_queues = {}


def _add_queue_if_not_exist(name: str) -> None:
    if name in _queues:
        return
    _queues[name] = Queue()


def _remove_queue(name: str) -> None:
    if name not in _queues:
        raise KeyError(f'There is no queue for "{name}"')
    del _queues[name]


def _pull(target: str, block: Optional[bool] = True, timeout: Optional[float] = None) -> IPCPackage:
    if target not in _queues:
        raise KeyError(f'There is no queue for "{target}"')
    queue: Queue = _queues[target]
    return queue.get(block=block, timeout=timeout)


def _put_manually(target: str, package: IPCPackage) -> None:
    if target not in _queues:
        raise KeyError(f'There is no queue for "{target}"')
    _queues[target].put(package)


def establish_connection(target: str, source: str, *, timeout: float = 5.0) -> IPCConnection:
    if target not in _queues:
        raise KeyError(f'Cannot establish connection: target "{target}" is not registered')

    logger = logging.getLogger(source)

    connection1, connection2 = Pipe()
    package = IPCPackage(command=_COMMAND_ESTABLISH)
    package.label(LABEL_IPC_SOURCE, source)
    package.pack(IPCConnection(connection2, target, source))

    _put_manually(target, package)

    connection = IPCConnection(connection1, source, target)
    ready_package = connection.recv(timeout=timeout)

    if ready_package is None:
        raise ConnectionError(f"{target} has not accepted connection")
    if ready_package.status != _STATUS_READY:
        raise ConnectionError(f"{target} has returned non-ready status")

    logger.debug(f"Established connection with {target}")
    return connection


class ExtensionHandlerIPCModule(ExtensionHandlerModule):

    def __init__(self, ipc_identifier: str):
        super().__init__()
        self._ipc_identifier = ipc_identifier
        _add_queue_if_not_exist(ipc_identifier)

        # maps all commands to their ipc_handlers
        self._ipc_handlers = {}

        self._worker = Thread(target=self._run)

        self._logger = logging.getLogger(ipc_identifier)

    def _on_load(self, extension: Extension):
        ipc_handler: IPCMessageHandler
        for ipc_handler in self._handlers[extension.name]:
            for ipc_command in ipc_handler.ipc_commands:
                if ipc_command in self._ipc_handlers:
                    raise ValueError(f"There is already a function registered for the "
                                     f"command '{ipc_command}'")
                self._ipc_handlers[ipc_command] = {"handler": ipc_handler, "extension": extension}

    def _on_unload(self, extension: Extension):
        ipc_handlers: IPCMessageHandler
        for ipc_handler in self._handlers[extension.name]:
            for ipc_command in ipc_handler.ipc_commands:
                self._ipc_handlers.pop(ipc_command)

    def get_accessible_types(self) -> list[str]:
        return ["IPCMessageHandler"]

    def _handle_connection(self, package: IPCPackage):
        self._logger.debug(f"Established connection with {package.labels[LABEL_IPC_SOURCE]}")

        connection: IPCConnection = package.content
        answer = IPCPackage(status=_STATUS_READY)

        while True:
            connection_package: IPCPackage = connection.send_and_recv(answer, timeout=60)

            if connection_package is None:
                self._logger.debug("Terminated connection")
                return

            command = connection_package.command
            handler_func = self._ipc_handlers[command]["handler"]
            extension = self._ipc_handlers[command]["extension"]

            try:
                result = handler_func(extension.extension, connection_package)
            except Exception as e:
                answer = IPCPackage(status="error").pack(e)
            else:
                answer = IPCPackage(status="ok").pack(result)

    def _run(self):
        while True:
            package: IPCPackage = _pull(self._ipc_identifier)
            command = package.command
            if command == _COMMAND_STOP:
                break
            elif command == _COMMAND_ESTABLISH:
                worker = Thread(target=self._handle_connection, args=(package,))
                worker.start()

    def start(self):
        self._worker.start()

    def stop(self):
        _put_manually(self._ipc_identifier, IPCPackage(command=_COMMAND_STOP))
        self._worker.join()
