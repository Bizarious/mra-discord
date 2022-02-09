from queue import Queue

from nextcord.ext import commands, tasks

from core import Bot, BOT_IDENTIFIER, SendTo
from core.ext import extension
from core.ext.modules import ipc
from core.ext.decorators import on_ipc_message
from core.permissions import owner
from core.task import FIELD_IPC_TASK_RESULT
from core.task.task_base import FIELD_CHANNEL


COMMAND_IPC_SEND = "send"


@extension(auto_load=True, target=BOT_IDENTIFIER)
class System(commands.Cog):
    """
    Provides commands for controlling the bot on the system level
    """

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self._send_queue = Queue()

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
    @owner()
    async def clear(self, ctx, n: int = 10):
        await ctx.channel.purge(limit=n)

    @tasks.loop(seconds=0.5)
    async def _send_loop(self):
        if not self._send_queue.empty():
            to_send = self._send_queue.get()
            identifier: int = to_send[0]
            destination: SendTo = to_send[1]
            message: str = to_send[2]
            await self.bot.send_to(destination, identifier, message)

    def on_load(self):
        self._send_loop.start()

    def on_unload(self):
        self._send_loop.cancel()

    @on_ipc_message(COMMAND_IPC_SEND)
    def _send(self, package: ipc.IPCPackage):
        message: str = package.content[FIELD_IPC_TASK_RESULT]
        channel: int = package.content[FIELD_CHANNEL]
        self._send_queue.put((channel, SendTo.CHANNEL, message))
