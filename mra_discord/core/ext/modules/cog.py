from nextcord import Message
from nextcord.ext.commands import Cog
from core.ext import Extension
from core.ext.modules import ExtensionHandlerModule


class ExtensionHandlerCogModule(ExtensionHandlerModule):

    def __init__(self, bot):
        super().__init__()

        self._bot = bot

        # old on_message method from bot
        self._old_on_message = self._bot.on_message

        async def on_message(message: Message):
            for cog, limiters in self._handlers.items():
                for limiter in limiters:
                    if not await limiter(cog, message):
                        return
            await self._old_on_message(message)

        self._bot.on_message = on_message

    def on_load_custom(self, extension: Extension):
        if isinstance(extension.extension, Cog):
            self._bot.add_cog(extension.extension)

    def on_unload_custom(self, extension: Extension):
        if isinstance(extension.extension, Cog):
            self._bot.remove_cog(extension.extension.qualified_name)

    def get_accessible_types(self) -> list[str]:
        return ["OnMessageLimiter"]
