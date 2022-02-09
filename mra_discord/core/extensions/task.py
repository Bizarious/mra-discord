from nextcord.ext import commands
from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.ext.modules import ipc
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER, \
    FIELD_DATE_STRING, FIELD_OWNER, FIELD_SOURCE, FIELD_CHANNEL
from tasks.reminder import FIELD_MESSAGE


_COMMAND_STOP = "stop"


@extension(auto_load=True, name="Task Handler", target=BOT_IDENTIFIER)
class TaskManager(commands.Cog):
    """
    Provides commands for managing tasks.
    """

    def __init__(self, bot: "Bot"):
        self._bot = bot
        self._task_handler = TaskHandler(["tasks"], ["core/extensions"])

    def on_load(self):
        self._task_handler.start()

    def on_unload(self):
        try:
            connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER, timeout=1)
            connection.send_and_recv(command=_COMMAND_STOP)
            connection.end_communication()
        except ConnectionError:
            # task handler was already stopped by external signal, so connection will fail
            pass
        self._task_handler.join()
        self._task_handler.extension_handler.cleanup()

    @commands.command()
    @owner()
    async def test(self, ctx: commands.Context):
        connection = ipc.establish_connection("task", BOT_IDENTIFIER)

        package = ipc.IPCPackage()
        package.pack(FIELD_OWNER, 0)
        package.pack(FIELD_DATE_STRING, "4s")
        package.pack(FIELD_MESSAGE, "Ha")
        package.pack(FIELD_SOURCE, BOT_IDENTIFIER)
        package.pack(FIELD_CHANNEL, ctx.channel.id)

        result = connection.send_and_recv(command="r", task="Reminder", package=package)
        print(result.content)

        package = ipc.IPCPackage()
        package.pack(FIELD_OWNER, 0)
        package.pack(FIELD_DATE_STRING, "2s")
        package.pack(FIELD_MESSAGE, "Bla")
        package.pack(FIELD_SOURCE, BOT_IDENTIFIER)
        package.pack(FIELD_CHANNEL, ctx.channel.id)

        result = connection.send_and_recv(command="r", task="Reminder", package=package)
        print(result.content)
        connection.end_communication()


@extension(auto_load=True, target=TASK_HANDLER_IDENTIFIER)
class TaskIPCHandler:

    def __init__(self, task_handler: TaskHandler):
        self._task_handler = task_handler

    @on_ipc_message("r")
    def test_ipc(self, package: ipc.IPCPackage):
        self._task_handler.add_task(package.labels["task"], package.content)

    @on_ipc_message(_COMMAND_STOP)
    def stop(self, _):
        self._task_handler.stop()
