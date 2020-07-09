from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    @commands.command()
    async def clear(self, ctx, n=5):
        await ctx.channel.purge(limit=n)


def setup(bot):
    bot.add_cog(Misc(bot))
