from nextcord.ext import commands

import tasks.reminder as reminder

from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.ext.modules import ipc
from core.extensions.system import CONTENT_FIELD_MESSAGE, CONTENT_FIELD_CHANNEL
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER, \
    TASK_FIELD_DATE_STRING, TASK_FIELD_OWNER, TASK_FIELD_SOURCE


_COMMAND_STOP = "stop"
COMMAND_CREATE_TASK = "create_task"

LABEL_TASK = "task"


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
            connection.send_and_recv(ipc.IPCPackage(command=_COMMAND_STOP))
            connection.end_communication()
        except ConnectionError:
            # task handler was already stopped by external signal, so connection will fail
            pass
        self._task_handler.join()

    @commands.command("rmdme")
    @owner()
    async def remind_me(self, ctx: commands.Context, date_string: str, message: str):
        content = {
            TASK_FIELD_OWNER: ctx.author.id,
            CONTENT_FIELD_CHANNEL: ctx.channel.id,
            TASK_FIELD_DATE_STRING: date_string,
            CONTENT_FIELD_MESSAGE: message,
        }

        connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER)
        connection.send_and_recv(ipc.IPCPackage(command=COMMAND_CREATE_TASK)
                                 .label(LABEL_TASK, reminder.TASK_NAME)
                                 .pack(content))
        connection.end_communication()


@extension(auto_load=True, target=TASK_HANDLER_IDENTIFIER)
class TaskIPCHandler:

    def __init__(self, task_handler: TaskHandler):
        self._task_handler = task_handler

    @on_ipc_message(COMMAND_CREATE_TASK)
    def create_task(self, package: ipc.IPCPackage):
        content = package.content
        content[TASK_FIELD_SOURCE] = package.labels[ipc.LABEL_IPC_SOURCE]
        self._task_handler.add_task(package.labels[LABEL_TASK], content)

    @on_ipc_message(_COMMAND_STOP)
    def stop(self, _):
        self._task_handler.stop()
