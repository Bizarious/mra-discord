import discord
from core.bot.errors import OnMessageCheckException, CmdParserException
from typing import Union
from discord.ext import commands, tasks
from core.permissions import Permissions
from core.database import Data, ConfigManager
from core.system import IPC
from core.containers import FctContainer
from core.bot.message_parser import MessageParser
from datetime import datetime as dt


def on_message_check(fct):
    return FctContainer(fct, "on_message")


def handle_ipc_commands(*args):
    def dec(fct):
        return FctContainer(fct, "parse_commands", *args)
    return dec


class BotClient(commands.Bot):
    def __init__(self, data, config, ipc: IPC):

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

        self.limit_cmd_processing = []
        self.cmd_parsers = {}   # contains functions + command strings
        self.cmd_parsers_mapping = {}   # contains command strings + cog names

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
            if pkt.cmd == "send":
                ctx = self.parser.parse(pkt.message, pkt.message_args)
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

    def add_limit(self, fct, cog,):
        self.limit_cmd_processing.append((fct, cog, cog.__cog_name__))

    def remove_limit(self, name: str):
        for i in range(len(self.limit_cmd_processing)):
            if self.limit_cmd_processing[i][2] == name:
                self.limit_cmd_processing.remove(self.limit_cmd_processing[i])

    def add_command_parser(self, fct, cog, *cmd: str):
        name = cog.__cog_name__
        for c in cmd:
            if c in self.cmd_parsers.keys():
                raise CmdParserException(f"The command '{c}' exists already.")
        if name not in self.cmd_parsers_mapping.keys():
            self.cmd_parsers_mapping[name] = []
        for c in cmd:
            self.cmd_parsers[c] = (fct, cog)
            self.cmd_parsers_mapping[name].append(c)

    def remove_command_parser(self, name: str):
        if name in self.cmd_parsers_mapping.keys():
            cmd = self.cmd_parsers_mapping[name]
            for c in cmd:
                del self.cmd_parsers[c]
            del self.cmd_parsers_mapping[name]

    def add_internal_checks(self, cog):
        for f in dir(cog):
            c = getattr(cog, f)
            if isinstance(c, FctContainer):
                if c.fct_add == "on_message":
                    self.add_limit(c.fct, cog)
                elif c.fct_add == "parse_commands":
                    self.add_command_parser(c.fct, cog, *c.args)

    def add_cog(self, cog):
        commands.Bot.add_cog(self, cog)
        self.add_internal_checks(cog)

    def remove_cog(self, name: str):
        commands.Bot.remove_cog(self, name)
        self.remove_limit(name)
        self.remove_command_parser(name)

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
