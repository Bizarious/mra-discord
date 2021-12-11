from nextcord.ext import commands
from core.ext import extension
from core.permissions import owner

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Bot


@extension(auto_load=True)
class System(commands.Cog):
    """
    Provides commands for controlling the bot on the system level
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot

    @commands.command()
    @owner()
    async def stop(self, _):
        """
        Stops the bot
        """
        await self.bot.stop()

    @commands.command()
    async def clear(self, ctx, n: int = 10):
        await ctx.channel.purge(limit=n)
