from .base import ExtensionHandlerModule
from typing import Any, TYPE_CHECKING
from core.ext.errors import IPCMessageHandlerError

if TYPE_CHECKING:
    from core.ext import IPCMessageHandler


class ExtensionHandlerIPCMixin(ExtensionHandlerModule):

    def __init__(self):
        self._accessible_types.append("IPCMessageHandler")

        # maps all ipc handlers to their commands
        self._ipc_handlers = {}
        self._ipc_handler_extensions = {}

        def on_load(attributes: dict, extension: Any):
            handlers: list[IPCMessageHandler] = attributes["IPCMessageHandler"]
            self._ipc_handler_extensions[extension.given_name] = []
            for handler in handlers:
                self._ipc_handler_extensions[extension.given_name].append(handler)
                for ipc_command in handler.ipc_commands:

                    if ipc_command in self._ipc_handlers:
                        raise IPCMessageHandlerError(f'There is already a function registered for the '
                                                     f'command "{ipc_command}"')

                    self._ipc_handlers[ipc_command] = handler

