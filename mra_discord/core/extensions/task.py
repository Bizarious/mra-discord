from typing import Callable, Optional

from nextcord import Embed
from nextcord.ext import commands

import tasks.reminder as reminder

from core import Bot, BOT_IDENTIFIER
from core.ext import extension
from core.ext.decorators import on_ipc_message
from core.ext.modules import ipc
from core.extensions.system import CONTENT_FIELD_MESSAGE
from core.permissions import owner
from core.task import TaskHandler, TASK_HANDLER_IDENTIFIER, TimeBasedTask, \
    TASK_FIELD_DATE_STRING, TASK_FIELD_OWNER, TASK_FIELD_SOURCE, TASK_FIELD_ID, TASK_FIELD_TYPE, \
    TASK_FIELD_NEXT_TIME, TASK_FIELD_CHANNEL
from core.utils.task import convert_task_field


_COMMAND_STOP = "stop"
COMMAND_CREATE_TASK = "create_task"
COMMAND_GET_TASKS = "get_tasks"

LABEL_TASK = "task"

FILTER_BY_AUTHOR = "author"
FILTER_BY_ID = "id"


def _generate_overview_embed(tasks: list[dict]) -> Embed:
    embed = Embed(title="Your tasks")
    for task_dict in tasks:
        value = "".join(
            f"`{field}:`\n{field_value}\n" for field, field_value in task_dict.items()
            if field in [TASK_FIELD_TYPE, TASK_FIELD_NEXT_TIME]
        )
        embed.add_field(name=task_dict[TASK_FIELD_ID], value=value)
    return embed


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
        if self._task_handler.is_alive():
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
            TASK_FIELD_CHANNEL: ctx.channel.id,
            CONTENT_FIELD_MESSAGE: message,
        }

        connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER)
        answer = connection.send_and_recv(
            ipc.IPCPackage(command=COMMAND_CREATE_TASK)
            .label(LABEL_TASK, reminder.TASK_NAME)
            .pack(content)
        )
        connection.end_communication()
        print(answer.content)

    def _generate_single_task_embed(self, tasks: list[dict]) -> Embed:
        task = tasks[0]
        embed = Embed(title=f"Task {task[TASK_FIELD_ID]}")
        for field, field_value in task.items():
            if field not in [TASK_FIELD_SOURCE]:
                embed.add_field(name=field, value=convert_task_field(field, field_value, self._bot))
        return embed

    @commands.command("gt")
    @owner()
    async def get_tasks(self, ctx: commands.Context, task_id: Optional[str] = None):
        filter_by = {
            FILTER_BY_AUTHOR: (ctx.author.id,),
        }
        if task_id is not None:
            filter_by[FILTER_BY_ID] = (task_id,)

        connection = ipc.establish_connection(TASK_HANDLER_IDENTIFIER, BOT_IDENTIFIER)
        answer = connection.send_and_recv(
            ipc.IPCPackage(command=COMMAND_GET_TASKS)
            .pack(filter_by)
        )
        connection.end_communication()

        tasks: list[dict] = answer.content
        if not tasks:
            if task_id is None:
                await ctx.send("You do not have any tasks")
            else:
                await ctx.send(f"You do not have a task with the id `{task_id}`")
        elif task_id is None:
            await ctx.send(embed=_generate_overview_embed(tasks))
        else:
            await ctx.send(embed=self._generate_single_task_embed(tasks))


def _filter_default(*_):
    def filter_default0(_):
        return True

    return filter_default0


def _filter_by_author(*authors: int):
    def filter_by_author0(task: TimeBasedTask):
        return task.author in authors
    return filter_by_author0


def _filter_by_id(*ids: str):
    def filter_by_id0(task: TimeBasedTask):
        return task.identifier in ids
    return filter_by_id0


def _apply_filters(*filter_functions: Callable[[TimeBasedTask], bool]) \
        -> Callable[[list[TimeBasedTask]], list[TimeBasedTask]]:
    def apply_filters0(tasks: list[TimeBasedTask]) -> list[TimeBasedTask]:
        result = tasks[:]
        for f in filter_functions:
            result = [task for task in result if f(task)]
        return result

    return apply_filters0


_TASK_FILTERS = {
    FILTER_BY_AUTHOR: _filter_by_author,
    FILTER_BY_ID: _filter_by_id,
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
