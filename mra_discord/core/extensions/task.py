from typing import Callable

from nextcord.ext import commands

import tasks.reminder as reminder

from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.ext.modules import ipc
from core.extensions.system import CONTENT_FIELD_MESSAGE, CONTENT_FIELD_CHANNEL
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER, TimeBasedTask, \
    TASK_FIELD_DATE_STRING, TASK_FIELD_OWNER, TASK_FIELD_SOURCE


_COMMAND_STOP = "stop"
COMMAND_CREATE_TASK = "create_task"
COMMAND_GET_TASKS = "get_tasks"

LABEL_TASK = "task"

FILTER_BY_AUTHOR = "author"


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
            TASK_FIELD_DATE_STRING: date_string,
            CONTENT_FIELD_CHANNEL: ctx.channel.id,
            CONTENT_FIELD_MESSAGE: message,
        }

        connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER)
        connection.send_and_recv(
            ipc.IPCPackage(command=COMMAND_CREATE_TASK)
            .label(LABEL_TASK, reminder.TASK_NAME)
            .pack(content)
        )
        connection.end_communication()

    @commands.command("gt")
    @owner()
    async def get_tasks(self, ctx: commands.Context):
        filter_by = {
            FILTER_BY_AUTHOR: (ctx.author.id,)
        }

        connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER)
        answer = connection.send_and_recv(
            ipc.IPCPackage(command=COMMAND_GET_TASKS)
            .pack(filter_by)
        )
        connection.end_communication()

        tasks: dict = answer.content
        print(tasks)


def _filter_default(*_):
    def filter_default0(_):
        return True
    return filter_default0


def _filter_by_author(*authors: int):
    def filter_by_author0(task: TimeBasedTask):
        return task.author in authors
    return filter_by_author0


def _apply_filters(*filter_functions: Callable[[TimeBasedTask], bool])\
        -> Callable[[list[TimeBasedTask]], list[TimeBasedTask]]:
    def apply_filters0(tasks: list[TimeBasedTask]) -> list[TimeBasedTask]:
        result = tasks[:]
        for f in filter_functions:
            result = [task for task in result if f(task)]
        return result
    return apply_filters0


_TASK_FILTERS = {
    FILTER_BY_AUTHOR: _filter_by_author
}


@extension(auto_load=True, target=TASK_HANDLER_IDENTIFIER)
class TaskIPCHandler:

    def __init__(self, task_handler: TaskHandler):
        self._task_handler = task_handler

    @on_ipc_message(COMMAND_CREATE_TASK)
    def create_task(self, package: ipc.IPCPackage):
        content = package.content
        content[TASK_FIELD_SOURCE] = package.labels[ipc.LABEL_IPC_SOURCE]
        self._task_handler.add_task(package.labels[LABEL_TASK], content)

    @on_ipc_message(COMMAND_GET_TASKS)
    def get_tasks(self, package: ipc.IPCPackage):
        filter_by = package.content
        filter_funcs = []
        for k, v in filter_by.items():
            f = _TASK_FILTERS.get(k, _filter_default)
            filter_funcs.append(f(*v))
        tasks = _apply_filters(*filter_funcs)(list(self._task_handler.get_all_tasks().values()))
        return [task.fields.raw_dict for task in tasks]

    @on_ipc_message(_COMMAND_STOP)
    def stop(self, _):
        self._task_handler.stop()
