from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.permissions import owner

import nextcord


__MANAGER_NAME = "Extension Manager"


class ExtensionEditDropdown(nextcord.ui.Select):

    def __init__(self, extension_manager: "ExtensionManager",
                 extension_view: "ExtensionManagementView",
                 mode: str
                 ):

        if mode == "load":
            max_values = extension_manager.get_number_of_unloaded_extensions()
            options = [
                nextcord.SelectOption(label=label)
                for label in extension_manager.get_unloaded_extensions()
            ]
        else:
            max_values = extension_manager.get_number_of_loaded_extensions(True)
            options = [
                nextcord.SelectOption(label=label)
                for label in extension_manager.get_loaded_extensions()
                if extension_manager.extension_handler.can_unload(label)
            ]

        super().__init__(placeholder=mode, min_values=1, max_values=max_values, options=options)

        self._extension_view = extension_view
        self._manager = extension_manager
        self._mode = mode

    async def callback(self, interaction: nextcord.Interaction):
        if self._mode == "load":
            for value in self.values:
                self._manager.extension_handler.load_extension(value)
        else:
            for value in self.values:
                self._manager.extension_handler.unload_extension(value)
        await self._extension_view.handle(interaction)


class ExtensionManagementView(nextcord.ui.View):

    def __init__(self, context: commands.Context, extension_manager: "ExtensionManager", mode: str):
        super().__init__(timeout=60)
        self._context = context
        self._manager = extension_manager
        self.add_item(ExtensionEditDropdown(extension_manager, self, mode))

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return self._context.author == interaction.user

    async def handle(self, interaction: nextcord.Interaction) -> None:
        self.clear_items()
        await interaction.response.edit_message(embed=self._manager.generate_extension_list(),
                                                view=self
                                                )


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
        all_extensions = list(self.extension_handler.extension_packages.keys())[:]
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
        all_ext = len(list(self.extension_handler.extension_packages.keys())[:])
        return all_ext - loaded

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
        await ctx.send(embed=embed, view=ExtensionManagementView(ctx, self, "load"))

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
        await ctx.send(embed=embed, view=ExtensionManagementView(ctx, self, "unload"))

    @commands.command("listext")
    @owner()
    async def list_extensions(self, ctx):
        """
        Lists all available extensions sorted by loaded/unloaded.
        """
        await ctx.send(embed=self.generate_extension_list())
