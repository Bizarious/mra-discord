from typing import TYPE_CHECKING
from nextcord.ext import commands
from core.ext import extension

if TYPE_CHECKING:
    from core import Bot


@extension(auto_load=True)
class BaseErrorHandler(commands.Cog):

    def __init__(self, bot: "Bot"):
        self._original_on_error = bot.on_command_error
        bot.on_command_error = self.on_command_error

    @staticmethod
    async def on_command_error(ctx: commands.Context, exception: commands.errors.CommandError) -> None:
        if isinstance(exception, commands.CheckFailure):
            await ctx.send("You do not have the permissions to issue this command.")
        else:
            await ctx.send(str(exception))

    def cog_unload(self) -> None:
        self.bot.on_command_error = self._original_on_error
