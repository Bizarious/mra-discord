from nextcord.ext import commands
from mra_discord.core.ext import extension


@extension(auto_load=True)
class System(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx: commands.Context):
        await ctx.send("Test")
