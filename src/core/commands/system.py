import os
from discord.ext import commands, tasks
from core.permissions import is_owner
from core.database import ConfigManager
from core.bot import handle_ipc_commands
from core.bot import service


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

        self.task_check = True

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command("prefix", hidden=True)
    @commands.check(is_owner)
    async def change_prefix(self, ctx, prefix):
        """
        Changes command prefix fot the server.
        """
        self.bot.change_prefix(prefix, ctx.message.guild.id)
        await ctx.send(f'Changed prefix for server "{self.bot.get_guild(ctx.message.guild.id).name}" to "{prefix}"')

    @handle_ipc_commands("shutdown", "restart")
    async def parse_commands(self, pkt):
        if pkt.cmd == "shutdown":
            await self.bot.shutdown()
        elif pkt.cmd == "restart":
            await self.bot.do_restart()

    @service("System-Checker")
    @tasks.loop(seconds=5)
    async def system_checker(self):
        if self.task_check:
            self.task_check = False
            pkt = self.bot.ipc.pack()
            pipe = self.bot.ipc.send(dst="task", package=pkt, cmd="ping", create_pipe=True)
            if pipe.poll(2) is False:
                await self.bot.send_to_admins("The task manager does not respond to ping. Please investigate.")


def setup(bot):
    bot.add_cog(System(bot))
