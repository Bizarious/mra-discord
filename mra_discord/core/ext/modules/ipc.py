from .base import ExtensionHandlerModule
from typing import Any, TYPE_CHECKING
from threading import Thread
from core.ipc import IPC, IPCPackage
from core.ext.errors import IPCMessageHandlerError

if TYPE_CHECKING:
    from core.ext import IPCMessageHandler


class ExtensionHandlerIPCModule(ExtensionHandlerModule):

    def __init__(self, ipc_handler: IPC, ipc_identifier: str):
        self._ipc_handler = ipc_handler
        self._ipc_handler.add_queue("")
        self._ipc_identifier = ipc_identifier

        # maps all ipc handlers to their commands
        self._ipc_handlers = {}
        self._ipc_handler_extensions = {}

    def on_load(self, attributes: dict, extension: Any):
        handlers: list[IPCMessageHandler] = attributes["IPCMessageHandler"]
        self._ipc_handler_extensions[extension.given_name] = []
        for handler in handlers:
            self._ipc_handler_extensions[extension.given_name].append(handler)
            for ipc_command in handler.ipc_commands:

                if ipc_command in self._ipc_handlers:
                    raise IPCMessageHandlerError(f'There is already a function registered for the '
                                                 f'command "{ipc_command}"')

                self._ipc_handlers[ipc_command] = handler

    def get_accessible_types(self) -> list[str]:
        return ["IPCMessageHandler"]

    def _handle_connection(self, package: IPCPackage):
        print(package)

    def _run(self):
        while True:
            package: IPCPackage = self._ipc_handler.pull(self._ipc_identifier)
            command = package.labels["command"]
            if command == "stop":
                return
            elif command == "establish":
                self._handle_connection(package)

    def start(self):
        worker = Thread(target=self._run)
        worker.start()

    def stop(self):
        pass
