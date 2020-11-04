import os
from typing import Union
from discord.ext import commands
from core.permissions import owner
from core.database import ConfigManager
from tabulate import tabulate as tab


class ExtensionHandler(commands.Cog, name="Cog Handler"):

    base_path = "./core/commands"
    base_import_path = "core.commands"

    name = "extension_handler.py"

    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config
        self.config.set_default_config("loadCogs", "none")
        self.paths = {"./extensions": "extensions"}
        self.loaded_cogs = {}

        self.load_base_ext()

        self.load_cogs = self.config.get_config("loadCogs")
        self.load_extra_ext()

    def list_all_extensions(self) -> dict:
        paths = {}
        for path in self.paths.keys():
            if os.path.exists(path):
                for f in os.listdir(path):
                    paths[f] = f"{self.paths[path]}.{f[:-3]}"
        return paths

    def get_ext(self, name: str) -> Union[str, None]:
        paths = self.list_all_extensions()
        for f in paths.keys():
            if f[:-3] == name and f.endswith(".py") and not f.startswith("__"):
                return paths[f]
        return None

    def load_base_ext(self):
        for f in os.listdir(self.base_path):
            if not f.startswith("__") and f != self.name and f.endswith(".py"):
                self.bot.load_extension(f"{self.base_import_path}.{f[:-3]}")

    def load_extra_ext(self):
        if self.load_cogs == "none":
            return
        paths = self.list_all_extensions()
        for f in paths.keys():
            if not f.startswith("__") and \
                    f.endswith(".py") and \
                    (f[:-3] in self.load_cogs or "all" in self.load_cogs):
                self.bot.load_extension(paths[f])
                self.loaded_cogs[f[:-3]] = paths[f]

    def get_available_ext(self) -> list:
        s = []
        paths = self.list_all_extensions()
        for f in paths.keys():
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
                if i in self.loaded_cogs.keys():
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
        cog_path = self.get_ext(cog)
        if cog_path is None:
            await ctx.send("Cog not found")
            return
        try:
            self.bot.load_extension(cog_path)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send("Cog is already loaded")
            return
        self.loaded_cogs[cog] = cog_path

    @commands.command("unload")
    @owner()
    async def unload_ext(self, ctx, cog):
        """
        Unloads specified extension.
        """
        if cog in self.loaded_cogs:
            self.bot.unload_extension(self.loaded_cogs[cog])
            del self.loaded_cogs[cog]
            return
        await ctx.send("Cog is not loaded")

    @commands.command("reload")
    @owner()
    async def reload_ext(self, ctx, cog):
        """
        Reloads specific extension.
        """
        if cog in self.loaded_cogs:
            self.bot.reload_extension(self.loaded_cogs[cog])
            return
        await ctx.send("Cog is not loaded")

    @commands.command("reloadall")
    @owner()
    async def reload_all_ext(self, _):
        """
        Reloads all loaded extensions.
        """
        for c in self.loaded_cogs.keys():
            self.bot.reload_extension(self.loaded_cogs[c])

    @commands.command("loadall")
    @owner()
    async def load_all_ext(self, _):
        """
        Loads all available extensions.
        """
        paths = self.list_all_extensions()
        for f in paths.keys():
            if not f.startswith("__") and f.endswith(".py"):
                try:
                    self.bot.load_extension(paths[f])
                    if f[:-3] not in self.loaded_cogs:
                        self.loaded_cogs[f[:-3]] = paths[f]
                except commands.ExtensionAlreadyLoaded:
                    pass

    @commands.command("unloadall")
    @owner()
    async def unload_all_ext(self, _):
        """
        Unloads all extensions.
        """
        for c in self.loaded_cogs:
            self.bot.unload_extension(self.loaded_cogs[c])
        self.loaded_cogs = {}


def setup(bot):
    bot.add_cog(ExtensionHandler(bot))
