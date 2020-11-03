import os
from discord.ext import commands
from core.permissions import owner
from core.database import ConfigManager
from tabulate import tabulate as tab


class ExtensionHandler(commands.Cog, name="Cog Handler"):

    base_path = "./core/commands"
    base_import_path = "core.commands"

    base_ext_path = "./extensions"
    base_ext_import_path = "extensions"
    name = "extension_handler.py"

    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config
        self.config.set_default_config("loadCogs", "none")
        self.loaded_cogs = []

        self.load_base_ext()

        self.load_cogs = self.config.get_config("loadCogs")
        self.load_extra_ext()

    def load_base_ext(self):
        for f in os.listdir(self.base_path):
            if not f.startswith("__") and f != self.name and f.endswith(".py"):
                self.bot.load_extension(f"{self.base_import_path}.{f[:-3]}")

    def load_extra_ext(self):
        if self.load_cogs == "none":
            return
        for f in os.listdir(self.base_ext_path):
            if not f.startswith("__") and \
                    f.endswith(".py") and \
                    (f[:-3] in self.load_cogs or "all" in self.load_cogs):
                self.bot.load_extension(f"{self.base_ext_import_path}.{f[:-3]}")
                self.loaded_cogs.append(f[:-3])

    def get_available_ext(self):
        s = []
        for f in os.listdir(self.base_ext_path):
            if not f.startswith("__"):
                s.append(f[:-3])
        return s

    @commands.command("listexts")
    async def list_extensions(self, ctx):
        """
        Lists all available extensions to load.
        """
        s: list = self.get_available_ext()
        if len(s) == 0:
            result = "No extensions found."
        else:
            headers = ["Available", "Loaded"]
            table = []

            loaded = []
            for i in s:
                if i in self.loaded_cogs:
                    loaded.append(i)
            s = [e for e in s if e not in loaded]

            length = len(s) - len(loaded)
            if length > 0:
                for i in range(length):
                    loaded.append("")
            elif length < 0:
                length = length * -1
                for i in range(length):
                    s.append("")

            for i in range(len(s)):
                table.append([s[i], loaded[i]])

            result = f"```{tab(table, headers=headers)}```"

        await ctx.send(result)

    @commands.command("load")
    @owner()
    async def load_ext(self, ctx, cog):
        """
        Loads specified extension.
        """
        for f in os.listdir(self.base_ext_path):
            if cog == f[:-3] and f.endswith(".py"):
                try:
                    self.bot.load_extension(f"{self.base_ext_import_path}.{cog}")
                except commands.ExtensionAlreadyLoaded:
                    await ctx.send("Cog is already loaded")
                    return
                self.loaded_cogs.append(cog)
                return
        await ctx.send("Cog not found")

    @commands.command("unload")
    @owner()
    async def unload_ext(self, ctx, cog):
        """
        Unloads specified extension.
        """
        if cog in self.loaded_cogs:
            self.bot.unload_extension(f"{self.base_ext_import_path}.{cog}")
            self.loaded_cogs.remove(cog)
            return
        await ctx.send("Cog is not loaded")

    @commands.command("loadall")
    @owner()
    async def load_all_ext(self, _):
        """
        Loads all available extensions.
        """
        for f in os.listdir(self.base_ext_path):
            if not f.startswith("__") and f.endswith(".py"):
                try:
                    self.bot.load_extension(f"{self.base_ext_import_path}.{f[:-3]}")
                    if f[:-3] not in self.loaded_cogs:
                        self.loaded_cogs.append(f[:-3])
                except commands.ExtensionAlreadyLoaded:
                    pass

    @commands.command("unloadall")
    @owner()
    async def unload_all_ext(self, _):
        """
        Unloads all extensions.
        """
        for f in self.loaded_cogs:
            self.bot.unload_extension(f"{self.base_ext_import_path}.{f}")
        self.loaded_cogs = []


def setup(bot):
    bot.add_cog(ExtensionHandler(bot))
