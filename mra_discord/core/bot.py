from nextcord.ext import commands
from typing import Any
from .data import DataProvider
from .permissions import Permissions
from core.ext import ExtensionHandler
from core.ext.mixins import ExtensionHandlerCogMixin

import nextcord


class BotExtensionHandler(ExtensionHandler, ExtensionHandlerCogMixin):

    def __init__(self, bot, *paths):
        ExtensionHandler.__init__(self, bot, *paths)
        ExtensionHandlerCogMixin.__init__(self)


class Bot(commands.Bot):

    def __init__(self, *,
                 command_prefix: str = ".",
                 extension_paths: list[str],
                 data_path: str,
                 intents: nextcord.Intents = nextcord.Intents.default()
                 ):

        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)

        # the extension handler used to manage all extensions
        self._extension_handler = BotExtensionHandler(self, *extension_paths)
        self._extension_handler.load_extensions_from_paths()

        # the data manager
        self._data_provider = DataProvider(data_path)

        # the permissions manager
        self._permissions = Permissions(self._data_provider)

        # flags
        self._running = False

    @property
    def data_provider(self):
        return self._data_provider

    @property
    def permissions(self):
        return self._permissions

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
