from nextcord.ext import commands
from typing import Any
from .data import DataProvider
from .permissions import Permissions
from .ipc import IPC
from core.ext import ExtensionHandler
from core.ext.modules import ExtensionHandlerCogModule

import nextcord

BOT_IDENTIFIER = "bot"


class Bot(commands.Bot):

    def __init__(self, *,
                 command_prefix: str = ".",
                 extension_paths: list[str],
                 data_path: str,
                 intents: nextcord.Intents = nextcord.Intents.default()
                 ):

        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)

        self._ipc_handler = IPC()

        self._extension_handler = ExtensionHandler(self, BOT_IDENTIFIER, *extension_paths)
        self._extension_handler.add_module(ExtensionHandlerCogModule(self))
        self._extension_handler.load_extensions_from_paths()

        self._data_provider = DataProvider(data_path)
        self._permissions = Permissions(self._data_provider)

        # flags
        self._running = False

    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider

    @property
    def permissions(self) -> Permissions:
        return self._permissions

    @property
    def extension_handler(self) -> ExtensionHandler:
        return self._extension_handler

    @property
    def ipc_handler(self) -> IPC:
        return self._ipc_handler

    async def on_ready(self):
        print("Ready")

    def run(self, *args: Any, **kwargs: Any) -> None:
        if self._running:
            raise RuntimeError("Bot is already running")
        self._running = True
        commands.Bot.run(self, *args, **kwargs)

    async def stop(self):
        self._extension_handler.unload_all_extensions()
        await self.close()

    async def register_bulk_application_commands(self) -> None:
        # seems to be abstract in base class
        pass
