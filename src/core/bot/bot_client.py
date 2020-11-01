import discord
from discord.ext import commands, tasks
from core.permissions import Permissions
from core.database import Data, ConfigManager
from core.system import IPC
from .message_parser import MessageParser


class BotClient(commands.Bot):
    def __init__(self, data, config, ipc: IPC):

        self.ipc = ipc

        self.default_prefix = "."
        self.data: Data = data  # database
        self.config: ConfigManager = config  # config

        self.prefixes = self.data.get_json(file="prefixes")
        intents = discord.Intents.default()
        intents.members = True

        commands.Bot.__init__(self, command_prefix=self.get_prefix, intents=intents)

        self.core_cogs_path = "./core/commands"
        self.core_import_cogs_path = "core.commands"
        self.permit = Permissions(self.data, self.config)
        self.parser = MessageParser()

        self.limit_cmd_processing = []

        self.bot_owner = self.permit.bot_owner

        # flags
        self.restart = False

        self.register_cog_handler()

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
                ctx = self.parser.parse(pkt.message, self)
                try:
                    if ctx.privacy == "public" and hasattr(pkt, "channel_id"):
                        if pkt.channel_id is not None:
                            await self.get_channel(pkt.channel_id).send(ctx.message)
                        else:
                            await self.get_user(pkt.author_id).send(ctx.message)
                    else:
                        await self.get_user(pkt.author_id).send(ctx.message)
                except Exception as e:
                    print(e)

    # Events
    async def on_ready(self):
        self.check_prefixes()
        await self.change_presence(status=discord.Status.online)
        self.background_loop.start()
        print("online")

    async def on_message(self, message):
        limits = []
        for limit in self.limit_cmd_processing:
            limits.append(limit[0](message))
        if all(limits):
            await self.process_commands(message)

    async def on_guild_join(self, guild):
        self.change_prefix(self.default_prefix, guild.id)

    async def on_command_error(self, ctx, exception):
        try:
            if isinstance(exception, commands.errors.CheckFailure):
                await ctx.send("No Permissions")
            elif isinstance(exception, commands.CommandInvokeError):
                if isinstance(exception.original, discord.Forbidden):
                    await ctx.send("I am not allowed to do that")
                else:
                    await ctx.send(exception.original)
            else:
                await ctx.send(exception)
        except discord.HTTPException:
            print("Cannot send error message due to network failure")

    # utility functions
    async def shutdown(self):
        await self.change_presence(status=discord.Status.offline)
        await self.logout()

    async def restart(self):
        self.restart = True
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
        self.data.set_json(file="prefixes", data=self.prefixes)

    def change_prefix(self, prefix, guild_id):
        self.prefixes[str(guild_id)] = prefix
        self.data.set_json(file="prefixes", data=self.prefixes)

    def register_cog_handler(self):
        self.load_extension("core.commands.cog_handler")

    def add_limit(self, fct, number):
        self.limit_cmd_processing.append((fct, number))

    def remove_limit(self, number):
        for i in range(len(self.limit_cmd_processing)):
            if self.limit_cmd_processing[i][1] == number:
                self.limit_cmd_processing.remove(self.limit_cmd_processing[i])

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
