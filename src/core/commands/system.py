import discord
import os
from discord.ext import commands
from core.permissions import owner
from core.system import measure_temp
from core.database import ConfigManager
from core.database.errors import ConfigNotExistentError


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

    @commands.command(hidden=True)
    @owner()
    async def shutdown(self, _, date_string=None):
        if date_string is None:
            await self.bot.shutdown()
        else:
            t = self.bot.ipc.pack(author_id=0, date_string=date_string)
            self.bot.ipc.send(dst="task", package=t, cmd="task", task="Shutdown", author_id=0)

    @commands.command(hidden=True)
    @owner()
    async def restart(self, _):
        self.bot.restart = True
        await self.bot.change_presence(status=discord.Status.offline)
        await self.bot.logout()

    @commands.command(hidden=True)
    @owner()
    async def update(self, ctx):
        m = os.popen("git pull").read()
        if "Already up to date" in m:
            await ctx.send("Already up to date.")
        else:
            await ctx.send("Updated")

    @commands.command("prefix", hidden=True)
    @owner()
    async def change_prefix(self, ctx, prefix):
        self.bot.change_prefix(prefix, ctx.message.guild.id)
        await ctx.send(f'Changed prefix for server "{self.bot.get_guild(ctx.message.guild.id).name}" to "{prefix}"')

    @commands.command("config")
    @owner()
    async def config_change(self, ctx, cmd, conf="", value=""):
        """
        Manages bot and command configurations
        """
        if cmd == "status":
            s = "```\nAll existent configs:\n\n"
            for c in self.config.configs.keys():
                s += f"{c} = {self.config.configs[c]}\n"
            s += "```"
            await ctx.send(s)

        elif cmd == "set":
            if conf == "":
                raise AttributeError(f"Conf must not be empty")
            if value == "":
                raise AttributeError(f"Value must not be empty")
            try:
                self.config.set_config(conf, value)
            except ConfigNotExistentError:
                await ctx.send(f"The config '{conf}' does not exist.")
            else:
                await ctx.send(f"Successfully changed '{conf}'. You may need to restart the bot.")

    @commands.command(hidden=True)
    @owner()
    async def temp(self, ctx):
        """
        Displays the cpu temperature.
        """
        try:
            temp = measure_temp()
        except ValueError:
            await ctx.send("This command is not available on this system.")
        else:
            await ctx.send(f'{temp} °C')
        

def setup(bot):
    bot.add_cog(System(bot))
