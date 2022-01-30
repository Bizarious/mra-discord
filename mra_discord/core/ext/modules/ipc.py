import logging
from typing import TYPE_CHECKING
from threading import Thread

from core.ext import Extension
from core.ext.modules import ExtensionHandlerModule
from core.ext.errors import IPCMessageHandlerError
from core.ipc import IPC, IPCPackage, IPCConnection

if TYPE_CHECKING:
    from core.ext.decorators import IPCMessageHandler


class ExtensionHandlerIPCModule(ExtensionHandlerModule):

    def __init__(self, ipc_handler: IPC, ipc_identifier: str):
        super().__init__()
        self._ipc_handler = ipc_handler
        self._ipc_handler.add_queue(ipc_identifier)
        self._ipc_identifier = ipc_identifier

        # maps all commands to their ipc_handlers
        self._ipc_handlers = {}

    def _on_load(self, extension: Extension):
        ipc_handler: IPCMessageHandler
        for ipc_handler in self._handlers[extension.name]:
            for ipc_command in ipc_handler.ipc_commands:
                if ipc_command in self._ipc_handlers:
                    raise IPCMessageHandlerError(f'There is already a function registered for the '
                                                 f'command "{ipc_command}"')
                self._ipc_handlers[ipc_command] = {"handler": ipc_handler, "extension": extension}

    def _on_unload(self, extension: Extension):
        ipc_handlers: IPCMessageHandler
        for ipc_handler in self._handlers[extension.name]:
            for ipc_command in ipc_handler.ipc_commands:
                self._ipc_handlers.pop(ipc_command)

    def get_accessible_types(self) -> list[str]:
        return ["IPCMessageHandler"]

    def _handle_connection(self, package: IPCPackage):
        logging.info("Established connection")

        connection: IPCConnection = package.content["connection"]

        while True:
            connection_package: IPCPackage = connection.recv(60)
            print(connection_package)

            if connection_package is None:
                logging.info("Terminated connection")
                return

            command = connection_package.labels["command"]
            handler_func = self._ipc_handlers[command]["handler"]
            extension = self._ipc_handlers[command]["extension"]

            try:
                answer = handler_func(extension, connection_package)
                if answer is None:
                    raise ValueError("ipc handler functions must return an ipc package")
            except BaseException as e:
                status = "error"
                answer = IPCPackage()
                answer.pack(error=e)
                connection.send(package=answer, status=status)
            else:
                status = "ok"
                connection.send(package=answer, status=status)

    def _run(self):
        while True:
            package: IPCPackage = self._ipc_handler.pull(self._ipc_identifier)
            command = package.labels["command"]
            if command == "stop":
                return
            elif command == "establish":
                worker = Thread(target=self._handle_connection, args=(package,))
                worker.start()

    def start(self):
        worker = Thread(target=self._run)
        worker.start()

    def stop(self):
        pass
