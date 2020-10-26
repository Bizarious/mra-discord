import discord
import os
from discord.ext import commands
from core.permissions import owner
from core.system.system_commands import measure_temp


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
