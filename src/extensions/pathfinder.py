from discord.ext import commands
import random


class Pathfinder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, number):
        limit = 5
        if "d" not in number:
            await ctx.send("False syntax. Use 'roll xdy'")
            return
        number = number.split("d")
        count = int(number[0])
        if count > limit:
            await ctx.send(f'No more than {limit} rolls allowed.')
        else:
            for _ in range(int(number[0])):
                await ctx.send(str(random.randint(1, int(number[1]))))


def setup(bot):
    bot.add_cog(Pathfinder(bot))
