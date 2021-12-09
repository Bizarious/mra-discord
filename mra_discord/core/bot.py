from nextcord.ext import commands
from mra_discord.core.ext import ExtensionHandler
from mra_discord.core.ext.mixins import ExtensionHandlerCogMixin


class BotExtensionHandler(ExtensionHandler, ExtensionHandlerCogMixin):

    def __init__(self, bot, *paths):
        ExtensionHandler.__init__(self, bot, *paths)
        ExtensionHandlerCogMixin.__init__(self)


class Bot(commands.Bot):

    def __init__(self, *, command_prefix: str = ".", paths: list[str]):
        commands.Bot.__init__(self, command_prefix=command_prefix)
        self._extension_handler = BotExtensionHandler(self, *paths)
        self._extension_handler.load_extensions_from_paths()
        self._extension_handler.load_extension("System")

    async def on_ready(self):
        print("Ready")

