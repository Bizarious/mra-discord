import os
import discord
from discord.ext import commands
from permissions import PermissionsDict
from multiprocessing import Queue
from containers import TransferPackage


class BotClient(commands.Bot):
    def __init__(self, data):
        # Queues
        self.queue_in: Queue = Queue()
        self.queue_task: Queue = Queue()
        self.queues = {"self": self.queue_in, "task": self.queue_task}

        self.default_prefix = "."
        self.data = data  # database
        self.prefixes = self.data.load("prefixes")
        commands.Bot.__init__(self, command_prefix=self.get_prefix)
        self.cogs_path = "./commands"
        self.register_cogs()
        self.restart = False
        self.permit = PermissionsDict(self.data)

        self.bot_owner = self.permit.bot_owner

    # Events
    async def on_ready(self):
        self.check_prefixes()
        await self.change_presence(status=discord.Status.online)
        print("online")

    async def on_message(self, message):
        a_id = message.author.id

        if a_id == self.bot_owner:
            await self.process_commands(message)
            return
        if a_id not in self.permit.users:
            if message.guild is None:
                return
            else:
                if message.guild.id not in self.permit.guilds and message.channel.id not in self.permit.channels:
                    await self.process_commands(message)

    async def on_guild_join(self, guild):
        self.change_prefix(self.default_prefix, guild.id)

    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.errors.CheckFailure):
            await ctx.send("No Permissions")
        else:
            await ctx.send(exception.__cause__)

    # utility functions
    async def get_prefix(self, message):
        if message.guild is None:
            return self.default_prefix
        return self.prefixes[str(message.guild.id)]

    def check_prefixes(self):
        for g in self.guilds:
            if str(g.id) not in self.prefixes:
                self.prefixes[str(g.id)] = self.default_prefix
        self.data.save(self.prefixes, "prefixes")

    def change_prefix(self, prefix, guild_id):
        self.prefixes[str(guild_id)] = prefix
        self.data.save(self.prefixes, "prefixes")

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

    def return_queue(self, queue):
        if queue == "bot":
            return self.queue_in
        elif queue == "task":
            return self.queue_task

    def send(self, *, dst, author, channel, **kwargs):
        t = TransferPackage(author=author, channel=channel, **kwargs)
        self.queues[dst].put(t)
