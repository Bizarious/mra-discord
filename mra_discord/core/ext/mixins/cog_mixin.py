from .base import ExtensionHandlerMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nextcord.ext.commands import Cog


class ExtensionHandlerCogMixin(ExtensionHandlerMixin):

    def __init__(self):
        self._to_be_executed_on_extension_loading.append(self.register_cog)

    def register_cog(self, _, cog: "Cog"):
        self._interface.add_cog(cog)
