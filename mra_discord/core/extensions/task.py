from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.permissions import owner
from core.task import TaskHandler


@extension(auto_load=True, name="Task Handler", target=BOT_IDENTIFIER)
class TaskHandler(commands.Cog):
    """
    Provides commands for managing tasks.
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        #self.t = TaskHandler(bot.ipc_handler)
        #self.t.start()

    @commands.command()
    @owner()
    async def test(self, ctx):
        self.bot.ipc_handler.establish_connection("task")


