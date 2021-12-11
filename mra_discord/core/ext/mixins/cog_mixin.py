from nextcord import Message
from nextcord.ext.commands import Cog
from .base import ExtensionHandlerMixin

from typing import Any


class ExtensionHandlerCogMixin(ExtensionHandlerMixin):

    def __init__(self):
        self._accessible_types.append("OnMessageLimiter")

        # holds all limiter objects
        self._limiter = {}

        def on_load(attributes: dict, extension: Any):
            if isinstance(extension, Cog):
                self._interface.add_cog(extension)

            self._limiter[extension.given_name] = []
            for limiter in attributes["OnMessageLimiter"]:
                self._limiter[extension.given_name].append(limiter)

        def on_unload(extension: Any):
            if isinstance(extension, Cog):
                self._interface.remove_cog(extension.qualified_name)

        self._to_be_executed_on_extension_loading.append(on_load)
        self._to_be_executed_on_extension_unloading.append(on_unload)

        self._old_on_message = self._interface.on_message

        async def on_message(message: Message):
            for cog, limiter_list in self._limiter.items():
                for limiter in limiter_list:
                    if not await limiter(cog, message):
                        return
            await self._old_on_message(message)

        self._interface.on_message = on_message
