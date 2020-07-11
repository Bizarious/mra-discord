import os
from discord.ext import commands
from .database import Data
from permissions import PermissionsDict


class BotClient(commands.Bot):
    def __init__(self):
        self.default_prefix = "."
        self.data = Data()
        self.prefixes = self.data.load_prefixes()
        commands.Bot.__init__(self, command_prefix=self.get_prefix)
        self.cogs_path = "./commands"
        self.register_cogs()
        self.restart = False
        self.permit = PermissionsDict(self.data)

    # Events
    async def on_ready(self):
        self.check_prefixes()
        print("online")
        print("Test")

    async def on_message(self, message):
        if message.guild.id not in self.permit.guilds and message.channel.id not in self.permit.channels and \
                message.author.id not in self.permit.users:
            await self.process_commands(message)

    async def on_guild_join(self, guild):
        self.change_prefix(self.default_prefix, guild.id)

    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.errors.CheckFailure):
            await ctx.send("No Permissions")
        else:
            await ctx.send(exception)

    # utility functions
    async def get_prefix(self, message):
        return self.prefixes[str(message.guild.id)]

    def check_prefixes(self):
        for g in self.guilds:
            if str(g.id) not in self.prefixes:
                self.prefixes[str(g.id)] = self.default_prefix
        self.data.save_prefixes(self.prefixes)

    def change_prefix(self, prefix, guild_id):
        self.prefixes[str(guild_id)] = prefix
        self.data.save_prefixes(self.prefixes)

    def register_cogs(self):
        for filename in os.listdir(self.cogs_path):
            if filename.endswith('.py') and not filename.startswith('_'):
                self.load_extension(f'commands.{filename[:-3]}')

    def get_guild_id(self, name):
        for g in self.guilds:
            if g.name == name:
                return g.id
        raise RuntimeError("Server not found")

    def get_channel_id(self, guild, channel):
        for g in self.guilds:
            for c in g.channels:
                if g.name == guild and c.name == channel:
                    return c.id
        raise RuntimeError("Channel not found")

    def get_user_id(self, name):
        for u in self.users:
            if u.name == name:
                return u.id
        raise RuntimeError("User not found")

# 'NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog'
