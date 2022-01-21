from nextcord.ext import commands
from core.ext import extension
from core.permissions import owner
from core.task import TaskHandler

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Bot


@extension(auto_load=True)
class Test(commands.Cog):
    """
    Provides commands for controlling the bot on the system level
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.t = TaskHandler(bot.ipc_handler)
        self.t.start()

    @commands.command()
    @owner()
    async def test(self, ctx):
        self.bot.ipc_handler.establish_connection("task")


