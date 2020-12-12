import discord
from core.bot.errors import OnMessageCheckException
from typing import Union
from discord.ext import commands, tasks
from core.permissions import Permissions
from core.database import Data, ConfigManager
from core.system import IPC
from core.bot.cog_method_handler import CogMethodHandler
from core.bot.message_parser import MessageParser
from datetime import datetime as dt


class BotClient(commands.Bot, CogMethodHandler):
    def __init__(self, data, config, ipc: IPC):
        CogMethodHandler.__init__(self)

        self.ipc = ipc

        self.start_time: dt = dt.now()

        self.default_prefix = "."
        self.data: Data = data  # database
        self.config: ConfigManager = config  # config

        self.prefixes = self.data.get_json(file="prefixes")
        intents = discord.Intents.default()
        intents.members = True

        commands.Bot.__init__(self, command_prefix=self.return_prefix, intents=intents)

        self.core_cogs_path = "./core/commands"
        self.core_import_cogs_path = "core.commands"
        self.permit = Permissions(self.data, self.config)
        self.parser = MessageParser()

        # flags
        self.restart = False

        self.register_cog_handler()

    # Loop
    @tasks.loop(seconds=0.2)
    async def background_loop(self):
        pkt = self.ipc.check_queue("bot")
        await self.parse_commands(pkt)

    async def send(self, pkt):
        # parses special arguments for message
        ctx = self.parser.parse(pkt.message, pkt.message_args)
        try:
            if ctx.privacy == "public" and hasattr(pkt, "channel_id"):
                if pkt.channel_id is not None:
                    await self.get_channel(pkt.channel_id).send(ctx.message)
                else:
                    # sends private, when no channel was specified
                    await self.get_user(pkt.author_id).send(ctx.message)
            else:
                await self.get_user(pkt.author_id).send(ctx.message)
        except Exception as e:
            print(e)

    async def parse_commands(self, pkt):
        if pkt is not None:
            if pkt.cmd == "send":
                await self.send(pkt)
            else:
                fct = self.cmd_parsers[pkt.cmd][0]
                cog = self.cmd_parsers[pkt.cmd][1]
                await fct(cog, pkt)

    # Events
    async def on_ready(self):
        # sending package to task manager to let it start
        t = self.ipc.pack()
        self.ipc.send(dst="task", package=t, cmd="start")

        self.check_prefixes()
        await self.change_presence(status=discord.Status.online)
        self.background_loop.start()
        print("online")

    async def on_disconnect(self):
        self.background_loop.cancel()

    async def on_message(self, message):
        limits = []
        # executes every limit function and checks, if they all return true
        for limit in self.limit_cmd_processing:
            result = await limit[0](limit[1], message)
            if not isinstance(result, bool):
                raise OnMessageCheckException("Your function must return a bool")
            limits.append(result)
        if all(limits):
            await self.process_commands(message)

    async def on_guild_join(self, guild):
        self.change_prefix(self.default_prefix, guild.id)

    async def on_command_error(self, ctx, exception):
        try:
            if isinstance(exception, commands.errors.CheckFailure):
                await ctx.send("You have not the permissions to issue this command.")
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

    async def do_restart(self):
        self.restart = True
        await self.change_presence(status=discord.Status.offline)
        await self.logout()

    def return_prefix(self, _, message):
        if message.guild is None:
            return self.default_prefix
        return self.prefixes[str(message.guild.id)]

    def return_prefix_message_only(self, message):
        """
        A wrapper for prefix return.
        """
        return self.return_prefix(None, message)

    def check_prefixes(self):
        for g in self.guilds:
            if str(g.id) not in self.prefixes:
                self.prefixes[str(g.id)] = self.default_prefix
        self.data.set_json(file="prefixes", data=self.prefixes)

    def change_prefix(self, prefix, guild_id: int):
        self.prefixes[str(guild_id)] = prefix
        self.data.set_json(file="prefixes", data=self.prefixes)

    def register_cog_handler(self):
        self.load_extension("core.commands.extension_handler")

    def add_cog(self, cog):
        commands.Bot.add_cog(self, cog)
        self.add_internal_checks(cog)

    def remove_cog(self, name: str):
        commands.Bot.remove_cog(self, name)
        self.remove_internal_checks(name)

    def get_guild_id(self, name: str) -> Union[int, None]:
        for g in self.guilds:
            if g.name == name:
                return g.id
        return None

    def get_channel_id(self, guild, channel) -> Union[int, None]:
        for g in self.guilds:
            for c in g.channels:
                if g.name == guild and c.name == channel:
                    return c.id
        return None

    def get_user_id(self, name) -> Union[int, None]:
        for u in self.users:
            if u.name == name:
                return u.id
        return None
