from .base import ExtensionHandlerMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nextcord.ext.commands import Cog


class ExtensionHandlerCogMixin(ExtensionHandlerMixin):

    def __init__(self):
        def load_cog(_, cog: "Cog"):
            self._interface.add_cog(cog)

        def unload_cog(cog: "Cog"):
            self._interface.remove_cog(cog.qualified_name)

        self._to_be_executed_on_extension_loading.append(load_cog)
        self._to_be_executed_on_extension_unloading.append(unload_cog)


