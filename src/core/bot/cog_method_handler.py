from core.containers import FctContainer
from core.bot.errors import CmdParserException
from discord.ext import tasks


def on_message_check(fct):
    return FctContainer(fct, "on_message")


def handle_ipc_commands(*args):
    def dec(fct):
        return FctContainer(fct, "parse_commands", *args)
    return dec


def service(name: str):
    def dec(fct):
        if not isinstance(fct, tasks.Loop):
            raise RuntimeError("A service must be a loop.")
        return FctContainer(fct, "service", name)
    return dec


class CogMethodHandler:

    def __init__(self):
        self.limit_cmd_processing = []
        self.cmd_parsers = {}  # contains functions -> command strings
        self.cmd_parsers_mapping = {}  # contains command strings -> cog names
        self.services = {}  # contains service name -> loop object

    def add_limit(self, fct, cog):
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

    def add_service(self, fct, cog, name: str):
        self.services[name] = [fct, cog, cog.__cog_name__]

    def remove_service(self, name: str):
        for i in self.services.keys():
            if self.services[i][2] == name:
                self.services[i][0].cancel()
                del self.services[i]

    def add_internal_checks(self, cog):
        for f in dir(cog):
            c = getattr(cog, f)
            if isinstance(c, FctContainer):
                if c.fct_add == "on_message":
                    self.add_limit(c.fct, cog)
                elif c.fct_add == "parse_commands":
                    self.add_command_parser(c.fct, cog, *c.args)
                elif c.fct_add == "service":
                    self.add_service(c.fct, cog, c.args[0])

    def remove_internal_checks(self, name: str):
        self.remove_limit(name)
        self.remove_command_parser(name)
        self.remove_service(name)
