import os
import sys
import logging

from typing import Any

import nextcord

from nextcord.ext import commands

from core.data import DataProvider
from core.permissions import Permissions
from core.ipc import IPC
from core.ext import ExtensionHandler
from core.ext.modules import ExtensionHandlerCogModule, ExtensionHandlerIPCModule

BOT_IDENTIFIER = "bot"

_logger = logging.getLogger(BOT_IDENTIFIER)


class Bot(commands.Bot):

    def __init__(self, *,
                 command_prefix: str = ".",
                 extension_paths: list[str],
                 data_path: str,
                 intents: nextcord.Intents = nextcord.Intents.all()
                 ):

        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)

        self._ipc_handler = IPC()

        self._extension_handler = ExtensionHandler(self, BOT_IDENTIFIER, *extension_paths)
        self._extension_handler.add_module(ExtensionHandlerCogModule(self))
        self._extension_handler.add_module(ExtensionHandlerIPCModule(self._ipc_handler, BOT_IDENTIFIER))
        self._extension_handler.load_extensions_from_paths()

        self._data_provider = DataProvider(data_path)
        self._permissions = Permissions(self._data_provider)

        # flags
        self._running = False
        self._restart = False

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

    @staticmethod
    async def on_ready():
        _logger.info("Logged in and ready")

    def run(self, *args: Any, **kwargs: Any) -> None:
        if self._running:
            raise RuntimeError("Bot is already running")
        self._running = True
        commands.Bot.run(self, *args, **kwargs)

        self._clean_up()

        if self._restart:
            _logger.info("Restarting")
            os.execv(sys.executable, [sys.executable.split("/")[-1]] + sys.argv)
        else:
            _logger.info("Shutting down")

    def _clean_up(self):
        self._extension_handler.unload_all_extensions()

    async def stop(self):
        self._extension_handler.unload_all_extensions()
        await self.close()

    async def restart(self):
        self._restart = True
        await self.stop()

    async def register_bulk_application_commands(self) -> None:
        # seems to be abstract in base class
        pass
