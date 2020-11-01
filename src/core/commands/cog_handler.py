import os
from discord.ext import commands
from core.permissions import owner
from core.database import ConfigManager


class CogHandler(commands.Cog, name="Cog Handler"):

    base_path = "./core/commands"
    base_import_path = "core.commands"

    base_cog_path = "./cogs"
    base_cog_import_path = "cogs"
    name = "cog_handler.py"

    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config
        self.config.set_default_config("loadCogs", "none")
        self.loaded_cogs = []

        self.load_base_cogs()

        self.load_cogs = self.config.get_config("loadCogs")
        self.load_extra_cogs()

    def load_base_cogs(self):
        for f in os.listdir(self.base_path):
            if not f.startswith("__") and f != self.name and f.endswith(".py"):
                self.bot.load_extension(f"{self.base_import_path}.{f[:-3]}")

    def load_extra_cogs(self):
        if self.load_cogs == "none":
            return
        for f in os.listdir(self.base_cog_path):
            if not f.startswith("__") and \
                    f.endswith(".py") and \
                    (f[:-3] in self.load_cogs or "all" in self.load_cogs):
                self.bot.load_extension(f"{self.base_cog_import_path}.{f[:-3]}")

    def get_available_cogs(self):
        s = ""
        for f in os.listdir(self.base_cog_path):
            if not f.startswith("__"):
                s += f"{f[:-3]}\n"
        return s

    @commands.command("listcogs")
    async def list_cogs(self, ctx):
        """
        Lists all available cogs to load
        """
        s = self.get_available_cogs()
        if s == "":
            result = "No cogs found."
        else:
            result = f"```\n{s}\n```"
        await ctx.send(result)

    @commands.command("loadcog")
    @owner()
    async def load_cog(self, ctx, cog):
        """
        Loads specified cog
        """
        for f in os.listdir(self.base_cog_path):
            if cog == f[:-3] and f.endswith(".py"):
                try:
                    self.bot.load_extension(f"{self.base_cog_import_path}.{cog}")
                except commands.ExtensionAlreadyLoaded:
                    await ctx.send("Cog is already loaded")
                    return
                self.loaded_cogs.append(cog)
                return
        await ctx.send("Cog not found")

    @commands.command("unloadcog")
    @owner()
    async def unload_cog(self, ctx, cog):
        """
        Unloads specified cog
        """
        if cog in self.loaded_cogs:
            self.bot.unload_extension(f"{self.base_cog_import_path}.{cog}")
            return
        await ctx.send("Cog is not loaded")

    @commands.command("loadall")
    @owner()
    async def load_all_cogs(self, _):
        """
        Loads all available cogs
        """
        for f in os.listdir(self.base_cog_path):
            if not f.startswith("__") and f.endswith(".py"):
                try:
                    self.bot.load_extension(f"{self.base_cog_import_path}.{f[:-3]}")
                    if f[:-3] not in self.loaded_cogs:
                        self.loaded_cogs.append(f[:-3])
                except commands.ExtensionAlreadyLoaded:
                    pass

    @commands.command("unloadall")
    @owner()
    async def unload_all_cogs(self, _):
        """
        Unloads all cogs
        """
        for f in self.loaded_cogs:
            self.bot.unload_extension(f"{self.base_cog_import_path}.{f}")


def setup(bot):
    bot.add_cog(CogHandler(bot))
