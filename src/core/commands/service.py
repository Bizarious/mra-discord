from discord.ext import commands, tasks
from tabulate import tabulate as tab
from core.permissions import is_owner
from core.database import ConfigManager
from core.bot import service


class ServiceManager(commands.Cog, name="Service Manager"):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

        self.config.set_default_config("defaultServices", "Services", "None")
        self.start_services = self.config.get_config("defaultServices", "Services")

    def start_default_services(self):
        if self.start_services == "None":
            return

        # split commas
        s = self.start_services.split(",")

        # remove spaces
        for i in range(len(s)):
            s[i] = s[i].replace(" ", "")

        # starting services
        for i in self.bot.services.keys():
            if i in s or "all" in s:
                svc = self.bot.services[i][0]
                c = self.bot.services[i][1]
                svc.start(c)

    @commands.command("enable")
    @commands.check(is_owner)
    async def enable_service(self, ctx, svc):
        """
        Enables the given service.
        """
        if svc not in self.bot.services.keys():
            raise RuntimeError("This service does not exist.")
        s = self.bot.services[svc][0]
        c = self.bot.services[svc][1]
        s.start(c)
        await ctx.send(f"started service '{svc}'.")

    @commands.command("disable")
    @commands.check(is_owner)
    async def disable_service(self, ctx, svc):
        """
        Disables the given service.
        """
        if svc not in self.bot.services.keys():
            raise RuntimeError("This service does not exist.")
        self.bot.services[svc][0].cancel()
        await ctx.send(f"canceled service '{svc}'.")

    @commands.command("listservices")
    @commands.check(is_owner)
    async def list_services(self, ctx):
        """
        Lists all available services.
        """
        s: list = self.bot.services.keys()
        if len(s) == 0:
            result = "No services found."
        else:
            headers = ["Available", "Running"]
            table = []
            a = []  # available, not running
            r = []  # running

            # filter running from not running
            for i in s:
                if self.bot.services[i][0].is_running():
                    r.append(i)
                else:
                    a.append(i)

            # calculating length difference
            # adding empty strings to fill places
            length = len(r) - len(a)
            if length > 0:
                for i in range(length):
                    a.append("")
            elif length < 0:
                length = length * -1
                for i in range(length):
                    r.append("")

            for i in range(len(r)):
                table.append([a[i], r[i]])

            result = f"```{tab(table, headers=headers)}```"

        await ctx.send(result)

    @commands.command("sds")
    @commands.check(is_owner)
    async def set_default_services(self, _, *, services):
        """
        Sets services, which shall be enabled by default.

        services:

            e.g. 'service1, service2'
        """
        self.config.set_config("defaultServices", "Services", services)

    @commands.Cog.listener()
    async def on_ready(self):
        self.start_default_services()

    @service("test")
    @tasks.loop(seconds=3)
    async def test_loop(self):
        print(42)

    @service("test2")
    @tasks.loop(seconds=3)
    async def test_loop2(self):
        print(1337)


def setup(bot):
    bot.add_cog(ServiceManager(bot))
