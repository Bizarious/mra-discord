import logging

from multiprocessing import Pipe, Queue
from multiprocessing.connection import Connection
from typing import TYPE_CHECKING, Optional, Any
from threading import Thread

from core.ext import Extension
from core.ext.modules import ExtensionHandlerModule

if TYPE_CHECKING:
    from core.ext.decorators import IPCMessageHandler

_FIELD_IPC_COMMAND = "command"
_FIELD_IPC_CONNECTION = "connection"
_FIELD_IPC_STATUS = "status"
_FIELD_IPC_SOURCE = "source"

_COMMAND_ESTABLISH = "establish"
_COMMAND_STOP = "stop"
_COMMAND_END_CONNECTION = "end"

_STATUS_READY = "ready"


class IPCPackage:
    """
    Offers a unified package interface in ipc communication.
    """

    def __init__(self):
        self._content = {}
        self._labels = {}

    def label(self, key, value):
        self._labels[key] = value

    def pack(self, key: str, value: Any):
        self._content[key] = value

    @property
    def labels(self):
        return self._labels

    @property
    def content(self):
        return self._content


class IPCConnection:

    def __init__(self, pipe: Connection, own_side: str, other_side: str):
        self._pipe = pipe
        self._own_side = own_side
        self._other_side = other_side
        self._logger = logging.getLogger(own_side)
        self._connection_running = True

    def _send(self, *,
              package: IPCPackage = IPCPackage(),
              command: Optional[str] = None,
              status: Optional[str] = None,
              **labels):

        if not self._connection_running:
            raise ConnectionError("This connection has already been terminated")

        package.label(_FIELD_IPC_COMMAND, command)
        package.label(_FIELD_IPC_STATUS, status)
        package.label(_FIELD_IPC_SOURCE, self._own_side)
        for k, v in labels.items():
            package.label(k, v)

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

        if package.labels[_FIELD_IPC_COMMAND] == _COMMAND_END_CONNECTION:
            self._logger.debug(f"Received connection end signal")
            self._connection_running = False
            return None

        return package

    def send_and_recv(self, *,
                      package: IPCPackage = IPCPackage(),
                      command: Optional[str] = None,
                      status: Optional[str] = None,
                      timeout: float = 5.0,
                      **labels):

        self._send(package=package, command=command, status=status, **labels)
        return self.recv(timeout)

    def end_communication(self):
        self._send(command=_COMMAND_END_CONNECTION)
        self._connection_running = False


_queues = {}


def _add_queue(name: str) -> None:
    if name in _queues:
        raise KeyError(f"There is already a queue for '{name}'")
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


def establish_connection(target: str, source: str) -> IPCConnection:
    if target not in _queues:
        raise KeyError(f'Cannot establish connection: target "{target}" is not registered')

    logger = logging.getLogger(source)

    connection1, connection2 = Pipe()
    package = IPCPackage()
    package.label(_FIELD_IPC_COMMAND, _COMMAND_ESTABLISH)
    package.label(_FIELD_IPC_SOURCE, source)
    package.pack(_FIELD_IPC_CONNECTION, IPCConnection(connection2, target, source))

    _queues[target].put(package)

    connection = IPCConnection(connection1, source, target)
    ready_package = connection.recv()

    if ready_package.labels[_FIELD_IPC_STATUS] != _STATUS_READY:
        raise ConnectionError(f"{target} has returned non-ready status")

    logger.debug(f"Established connection with {target}")
    return connection


class ExtensionHandlerIPCModule(ExtensionHandlerModule):

    def __init__(self, ipc_identifier: str):
        _add_queue(ipc_identifier)
        super().__init__()
        self._ipc_identifier = ipc_identifier

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
        self._logger.debug(f"Established connection with {package.labels[_FIELD_IPC_SOURCE]}")

        connection: IPCConnection = package.content[_FIELD_IPC_CONNECTION]
        status = _STATUS_READY
        answer = IPCPackage()

        while True:
            connection_package: IPCPackage = connection.send_and_recv(status=status, package=answer, timeout=60)

            if connection_package is None:
                self._logger.debug("Terminated connection")
                return

            command = connection_package.labels[_FIELD_IPC_COMMAND]
            handler_func = self._ipc_handlers[command]["handler"]
            extension = self._ipc_handlers[command]["extension"]

            try:
                maybe_answer = handler_func(extension.extension, connection_package)
            except BaseException as e:
                status = "error"
                answer = IPCPackage()
                answer.pack("error", e)
            else:
                status = "ok"
                if maybe_answer is None:
                    answer = IPCPackage()
                else:
                    answer = maybe_answer

    def _run(self):
        while True:
            package: IPCPackage = _pull(self._ipc_identifier)
            command = package.labels[_FIELD_IPC_COMMAND]
            if command == _COMMAND_STOP:
                break
            elif command == _COMMAND_ESTABLISH:
                worker = Thread(target=self._handle_connection, args=(package,))
                worker.start()

    def start(self):
        self._worker.start()

    def stop(self):
        package = IPCPackage()
        package.label(_FIELD_IPC_COMMAND, _COMMAND_STOP)
        _put_manually(self._ipc_identifier, package)
        self._worker.join()

    def cleanup(self):
        _remove_queue(self._ipc_identifier)
