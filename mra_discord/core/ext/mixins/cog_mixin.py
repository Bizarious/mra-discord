from nextcord import Message
from .base import ExtensionHandlerMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nextcord.ext.commands import Cog


class ExtensionHandlerCogMixin(ExtensionHandlerMixin):

    def __init__(self):
        self._accessible_types.append("OnMessageLimiter")

        # holds all limiter objects
        self._limiter = {}

        def on_load(attributes: dict, cog: "Cog"):
            self._interface.add_cog(cog)

            self._limiter[cog.qualified_name] = []
            for limiter in attributes["OnMessageLimiter"]:
                self._limiter[cog.qualified_name].append(limiter)

        def on_unload(cog: "Cog"):
            self._interface.remove_cog(cog.qualified_name)

        self._to_be_executed_on_extension_loading.append(on_load)
        self._to_be_executed_on_extension_unloading.append(on_unload)

        async def on_message(message: Message):
            for cog, limiter_list in self._limiter.items():
                for limiter in limiter_list:
                    if not await limiter(cog, message):
                        return
            await self._interface.process_commands(message)

        self._old_on_message = self._interface.on_message
        self._interface.on_message = on_message
