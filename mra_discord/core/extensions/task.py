from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.ext.modules import ipc
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER, \
    FIELD_DATE_STRING, FIELD_OWNER
from tasks.reminder import FIELD_MESSAGE


@extension(auto_load=True, name="Task Handler", target=BOT_IDENTIFIER)
class TaskManager(commands.Cog):
    """
    Provides commands for managing tasks.
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.t = TaskHandler(["tasks"], ["core/extensions"])

    def on_load(self):
        self.t.start()

    def on_unload(self):
        self.t.terminate()
        self.t.join()

    @commands.command()
    @owner()
    async def test(self, ctx):
        connection = ipc.establish_connection("task", BOT_IDENTIFIER)

        package = ipc.IPCPackage()
        package.pack(FIELD_OWNER, 0)
        package.pack(FIELD_DATE_STRING, "* * * * * *")
        package.pack(FIELD_MESSAGE, "Ha")

        connection.send(command="r", task="Reminder", package=package)
        connection.end_communication()


@extension(auto_load=True, target=TASK_HANDLER_IDENTIFIER)
class TaskIPCHandler:

    def __init__(self, task_handler: TaskHandler):
        self._task_handler = task_handler

    @on_ipc_message("r")
    def test_ipc(self, package: ipc.IPCPackage):
        self._task_handler.add_task(package.labels["task"], package.content)
