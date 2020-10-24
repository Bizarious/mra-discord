import os
import discord
from discord.ext import commands, tasks
from permissions import PermissionsDict
from system.ipc import IPC


class BotClient(commands.Bot):
    def __init__(self, data, ipc: IPC):

        self.ipc = ipc
        self.default_prefix = "."
        self.data = data  # database
        self.prefixes = self.data.load("prefixes")
        commands.Bot.__init__(self, command_prefix=self.get_prefix)
        self.cogs_path = "./commands"
        self.register_cogs()
        self.restart = False
        self.permit = PermissionsDict(self.data)

        self.bot_owner = self.permit.bot_owner

    # Loop
    @tasks.loop(seconds=0.2)
    async def background_loop(self):
        pkt = self.ipc.check_queue("bot")
        await self.parse_commands(pkt)

    async def parse_commands(self, pkt):
        if pkt is not None:
            if pkt.cmd == "shutdown":
                await self.shutdown()
            elif pkt.cmd == "send":
                if pkt.channel_id is not None:
                    await self.get_channel(pkt.channel_id).send(pkt.message)
                else:
                    await self.get_user(pkt.author_id).send(pkt.message)

    # Events
    async def on_ready(self):
        self.check_prefixes()
        await self.change_presence(status=discord.Status.online)
        self.background_loop.start()
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
            await ctx.send(exception)

    # utility functions
    async def shutdown(self):
        await self.change_presence(status=discord.Status.offline)
        await self.logout()

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
