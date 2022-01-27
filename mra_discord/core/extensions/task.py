from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ipc import IPCPackage
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER


@extension(auto_load=False, name="Task Handler", target=BOT_IDENTIFIER)
class TaskManager(commands.Cog):
    """
    Provides commands for managing tasks.
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.t = TaskHandler(bot.ipc_handler, [], ["core/extensions"])
        self.t.start()

    @commands.command()
    @owner()
    async def test(self, ctx):
        connection = self.bot.ipc_handler.establish_connection("task", "bot")
        connection.send(command="test")
        connection.recv()
        connection.send(command="test")
        connection.recv()
        connection.end_communication()


@extension(auto_load=True, target=TASK_HANDLER_IDENTIFIER)
class TaskIPCHandler:

    def __init__(self, task_handler: TaskHandler):
        self._task_handler = task_handler

    @on_ipc_message("test")
    def test_ipc(self, package: IPCPackage):
        print(package.labels)
        print("test")
