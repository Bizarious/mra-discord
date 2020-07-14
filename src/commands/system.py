import os
from discord.ext import commands
from permissions import is_it_me
from system_commands import measure_temp


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_it_me()
    async def shutdown(self, _):
        await self.bot.logout()

    @commands.command()
    @is_it_me()
    async def restart(self, _):
        self.bot.restart = True
        await self.bot.logout()

    @commands.command()
    @is_it_me()
    async def update(self, ctx):
        status = str(os.popen("git pull --ff-only").read())
        if "Already up to date." in status:
            await ctx.send(status)
        else:
            await ctx.send("Updated.")

    @commands.command("prefix")
    @is_it_me()
    async def change_prefix(self, ctx, prefix):
        self.bot.change_prefix(prefix, ctx.message.guild.id)
        await ctx.send(f'Changed prefix for server "{self.bot.get_guild(ctx.message.guild.id).name}" to "{prefix}"')

    @commands.command()
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
