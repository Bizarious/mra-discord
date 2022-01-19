from nextcord import Message
from nextcord.ext.commands import Cog
from .base import ExtensionHandlerModule

from typing import Any


class ExtensionHandlerCogModule(ExtensionHandlerModule):

    def __init__(self, bot):
        self._bot = bot

        # holds all limiter objects
        self._limiter = {}

        # old on_message method from bot
        self._old_on_message = self._bot.on_message

        async def on_message(message: Message):
            for cog, limiter_list in self._limiter.items():
                for limiter in limiter_list:
                    if not await limiter(cog, message):
                        return
            await self._old_on_message(message)

        self._bot.on_message = on_message

    def on_load(self, attributes: dict, extension: Any):
        if isinstance(extension, Cog):
            self._bot.add_cog(extension)

        self._limiter[extension.given_name] = []
        for limiter in attributes["OnMessageLimiter"]:
            self._limiter[extension.given_name].append(limiter)

    def on_unload(self, extension: Any):
        if isinstance(extension, Cog):
            self._bot.remove_cog(extension.qualified_name)

    def get_accessible_types(self) -> list[str]:
        return ["OnMessageLimiter"]
