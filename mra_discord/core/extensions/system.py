from typing import TYPE_CHECKING
from nextcord.ext import commands
from mra_discord.core.ext import extension
from core.permissions import owner

if TYPE_CHECKING:
    from core import Bot


@extension(auto_load=True)
class System(commands.Cog):

    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.command()
    @owner()
    async def stop(self, _):
        await self.bot.stop()

    @commands.command()
    async def clear(self, ctx, n: int = 10):
        await ctx.channel.purge(limit=n)
