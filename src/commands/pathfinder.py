from discord.ext import commands
import random


class Pathfinder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, number):
        number = number.split("d")
        for _ in range(int(number[0])):
            await ctx.send(str(random.randint(1, int(number[1]))))


def setup(bot):
    bot.add_cog(Pathfinder(bot))
