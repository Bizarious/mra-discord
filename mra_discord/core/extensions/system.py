from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.permissions import owner


@extension(auto_load=True, target=BOT_IDENTIFIER)
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
        Stops the bot.
        """
        await self.bot.stop()

    @commands.command()
    @owner()
    async def restart(self, _):
        """
        Restarts the bot.
        """
        await self.bot.restart()

    @commands.command()
    async def clear(self, ctx, n: int = 10):
        await ctx.channel.purge(limit=n)
