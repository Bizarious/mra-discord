import os
from discord.ext import commands
from core.permissions import is_owner
from core.system import measure_temp
from core.database import ConfigManager
from core.database.errors import ConfigNotExistentError
from core.bot import handle_ipc_commands


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

    @commands.command()
    @commands.check(is_owner)
    async def shutdown(self, _, date_string=None):
        """
        Shuts down the bot.

        date_string:
            Specifying this wil create a system task instead of shutting down the bot immediately.
            Run 'help tasks' for further information.
        """
        if date_string is None:
            await self.bot.shutdown()
        else:
            t = self.bot.ipc.pack(author_id=0, date_string=date_string, mode="shutdown")
            self.bot.ipc.send(dst="task", package=t, cmd="task", task="Shutdown", author_id=0)

    @commands.command()
    @commands.check(is_owner)
    async def restart(self, _, date_string=None):
        """
        Restarts the bot.

        date_string:
            Specifying this wil create a system task instead of restarting the bot immediately.
            Run 'help tasks' for further information.
        """
        if date_string is None:
            await self.bot.do_restart()
        else:
            t = self.bot.ipc.pack(author_id=0, date_string=date_string, mode="restart")
            self.bot.ipc.send(dst="task", package=t, cmd="task", task="Shutdown", author_id=0)

    @commands.command()
    @commands.check(is_owner)
    async def update(self, ctx):
        """
        Pulls changes from git.
        """
        m = os.popen("git pull").read()
        if "Already up to date" in m:
            await ctx.send("Already up to date.")
        else:
            await ctx.send("Updated")

    @commands.command("prefix")
    @commands.check(is_owner)
    async def change_prefix(self, ctx, prefix):
        """
        Changes command prefix fot the server.
        """
        self.bot.change_prefix(prefix, ctx.message.guild.id)
        await ctx.send(f'Changed prefix for server "{self.bot.get_guild(ctx.message.guild.id).name}" to "{prefix}"')

    """""""""
    @commands.command("config")
    @commands.check(is_owner)
    async def config_change(self, ctx, cmd, conf="", value=""):
        
        Manages bot and command configurations.

        cmd:

            status: Shows all existing configs and there values.
            set: Modifies a config value.

        conf:

            The config to be modified.

        value:

            The value to be set.
        
        if cmd == "status":
            s = "```\nAll existent configs:\n\n"
            for c in self.config.configs.keys():
                s += f"{c} = {self.config.configs[c]}\n"
            s += "```"
            await ctx.send(s)

        elif cmd == "set":
            if conf == "":
                raise RuntimeError(f"Conf must not be empty")
            if value == "":
                raise RuntimeError(f"Value must not be empty")
            try:
                self.config.set_config(conf, value)
            except ConfigNotExistentError:
                await ctx.send(f"The config '{conf}' does not exist.")
            else:
                await ctx.send(f"Successfully changed '{conf}'. You may need to restart the bot.")
        else:
            await ctx.send(f"'{cmd}' is no valid argument.")
    """""""""

    @commands.command()
    @commands.check(is_owner)
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

    @handle_ipc_commands("shutdown", "restart")
    async def parse_commands(self, pkt):
        if pkt.cmd == "shutdown":
            await self.bot.shutdown()
        elif pkt.cmd == "restart":
            await self.bot.do_restart()
        

def setup(bot):
    bot.add_cog(System(bot))
