import os
from discord.ext import commands


class BotClient(commands.Bot):
    def __init__(self):
        commands.Bot.__init__(self, command_prefix=".")
        self.cogs_path = "./commands"
        self.register_cogs()
        self.restart = False

    async def on_ready(self):
        print("online")

    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.errors.CheckFailure):
            await ctx.send("No Permissions")

    def register_cogs(self):
        for filename in os.listdir(self.cogs_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                self.load_extension(f'commands.{filename[:-3]}')


# 'NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog'
