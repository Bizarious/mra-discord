from discord.ext import commands
import random


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    @commands.command()
    async def clear(self, ctx, n=5, mode=None):
        if mode is None:
            async for m in ctx.message.channel.history(limit=n):
                if m.author == self.bot.user or m.content.startswith(self.bot.prefixes[str(ctx.message.guild.id)]):
                    await m.delete()
        elif mode == "all":
            await ctx.channel.purge(limit=n)

    @commands.command()
    async def choose(self, ctx):
        guild = self.bot.get_guild(ctx.message.guild.id)
        vc = guild.voice_channels
        for c in vc:
            for m in c.members:
                if m.id == ctx.message.author.id:
                    i = random.randint(0, len(c.members)-1)
                    await ctx.send(c.members[i].mention)
                    return
        await ctx.send("You are not in a voice-channel.")


def setup(bot):
    bot.add_cog(Misc(bot))