from discord import DMChannel
from discord.ext import commands
import random
import asyncio
from core.version import __version__


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    @commands.command()
    async def clear(self, ctx, n=5, mode=None):

        def message_check(m):
            if m.author == self.bot.user or m.content.startswith(self.bot.prefixes[str(ctx.message.guild.id)]):
                return True
            return False

        if not isinstance(ctx.channel, DMChannel):
            if mode is None:
                await ctx.channel.purge(limit=n, check=message_check)
            elif mode == "all":
                await ctx.channel.purge(limit=n)
        else:
            async for message in ctx.author.dm_channel.history(limit=n):
                if message.author == self.bot.user:
                    await message.delete()
                    await asyncio.sleep(0.2)

    @commands.command()
    async def version(self, ctx):
        await ctx.send(__version__)

    @commands.command()
    async def choose(self, ctx, amount=0):
        """
        Chooses randomly a member of the voice-channel you are in and mentions it.
        """
        if amount > 10000:
            raise RuntimeError("Number of rolls must not be greater than 10000.")
        guild = self.bot.get_guild(ctx.message.guild.id)
        vc = guild.voice_channels
        for c in vc:
            for m in c.members:
                if m.id == ctx.message.author.id:
                    if amount == 0:
                        i = random.randint(0, len(c.members) - 1)
                        await ctx.send(c.members[i].mention)
                        return
                    else:
                        amount_list = []
                        for _ in range(amount):
                            amount_list.append(random.randint(0, len(c.members) - 1))
                        for i in range(len(c.members)):
                            await ctx.send(c.members[i].mention + f': {amount_list.count(i)}')
                        return

        await ctx.send("You are not in a voice-channel.")


def setup(bot):
    bot.add_cog(Misc(bot))
