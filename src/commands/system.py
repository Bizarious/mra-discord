from discord.ext import commands
from permissions import is_it_me


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return is_it_me(ctx)

    @commands.command()
    async def shutdown(self, _):
        await self.bot.logout()

    @commands.command()
    async def restart(self, _):
        self.bot.restart = True
        await self.bot.logout()


def setup(bot):
    bot.add_cog(System(bot))
