from nextcord.ext import commands
from core.ext import ExtensionHandler
from core.ext.mixins import ExtensionHandlerCogMixin

import nextcord
import core.data as data


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
        self._extension_handler.load_extension("System")

        # the data manager
        self._data_provider = data.DataProvider(data_path)

        # flags
        self._running = False

    async def on_ready(self):
        print("Ready")
