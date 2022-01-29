import nextcord
from nextcord.ext import commands

from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.permissions import owner
from core.utils import InteractionView


__MANAGER_NAME = "Extension Manager"


@extension(name=__MANAGER_NAME, auto_load=True, can_unload=False, target=BOT_IDENTIFIER)
class ExtensionManager(commands.Cog, name=__MANAGER_NAME):
    """
    Used to manage installed extensions
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.extension_handler = bot.extension_handler

    def get_loaded_extensions(self) -> list[str]:
        return list(self.extension_handler.loaded_extensions.keys())[:]

    def get_unloaded_extensions(self) -> list[str]:
        loaded_extensions = self.get_loaded_extensions()
        all_extensions = list(self.extension_handler.extensions.keys())[:]
        return [e for e in all_extensions if e not in loaded_extensions]

    def generate_extension_list(self) -> nextcord.Embed:
        loaded_extensions = self.get_loaded_extensions()
        not_loaded_extensions = self.get_unloaded_extensions()

        embed = nextcord.Embed(title="Extension Table")
        embed.add_field(name="Loaded",
                        value=" ".join(f"`{e}`" for e in loaded_extensions) or "---",
                        inline=False
                        )
        embed.add_field(name="Not Loaded",
                        value=" ".join(f"`{e}`" for e in not_loaded_extensions) or "---",
                        inline=False
                        )

        return embed

    def get_number_of_loaded_extensions(self, ignore_cannot_unload: bool = False) -> int:
        extensions = list(self.extension_handler.loaded_extensions.keys())[:]
        if not ignore_cannot_unload:
            return len(extensions)
        return len([e for e in extensions if self.extension_handler.can_unload(e)])

    def get_number_of_unloaded_extensions(self) -> int:
        loaded = self.get_number_of_loaded_extensions()
        all_ext = len(list(self.extension_handler.extensions.keys())[:])
        return all_ext - loaded

    def _load_extensions(self, extensions: list[str]):
        for ext in extensions:
            self.extension_handler.load_extension(ext)

    @commands.command("load")
    @owner()
    async def load_extension(self, ctx):
        """
        Provides an interactive interface for loading extensions.
        """
        if self.get_number_of_unloaded_extensions() == 0:
            await ctx.send("There are no extensions left that could be loaded.")
            return

        embed = self.generate_extension_list()

        options = [{"label": ext} for ext in self.get_unloaded_extensions()]

        view = InteractionView(ctx)
        view.set_embed_generator(self.generate_extension_list)
        view.add_dropdown(self._load_extensions,
                          "Choose extension to load",
                          options,
                          max_values=len(options)
                          )

        await ctx.send(embed=embed, view=view)

    def _unload_extensions(self, extensions: list[str]):
        for ext in extensions:
            self.extension_handler.unload_extension(ext)

    @commands.command("unload")
    @owner()
    async def unload_extension(self, ctx):
        """
        Provides an interactive interface for loading extensions.
        """
        if self.get_number_of_loaded_extensions(True) == 0:
            await ctx.send("There are no extensions left that could be unloaded.")
            return

        embed = self.generate_extension_list()

        options = [{"label": ext} for ext in self.get_loaded_extensions() if self.extension_handler.can_unload(ext)]

        view = InteractionView(ctx)
        view.set_embed_generator(self.generate_extension_list)
        view.add_dropdown(self._unload_extensions,
                          "Choose extension to unload",
                          options,
                          max_values=len(options)
                          )

        await ctx.send(embed=embed, view=view)

    @commands.command("listext")
    @owner()
    async def list_extensions(self, ctx):
        """
        Lists all available extensions sorted by loaded/unloaded.
        """
        await ctx.send(embed=self.generate_extension_list())
