from discord.ext import commands
from tabulate import tabulate as tab
from core.permissions import is_owner
from core.database import ConfigManager


class ServiceManager(commands.Cog, name="Service Manager"):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

    @commands.command("enable")
    @commands.check(is_owner)
    async def enable_service(self, ctx, service):
        """
        Enables the given service.
        """
        if service not in self.bot.services.keys():
            raise RuntimeError("This service does not exist.")
        s = self.bot.services[service][0]
        c = self.bot.services[service][1]
        s.start(c)
        await ctx.send(f"started service '{service}'.")

    @commands.command("disable")
    @commands.check(is_owner)
    async def disable_service(self, ctx, service):
        """
        Disables the given service.
        """
        if service not in self.bot.services.keys():
            raise RuntimeError("This service does not exist.")
        self.bot.services[service][0].cancel()
        await ctx.send(f"canceled service '{service}'.")

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


def setup(bot):
    bot.add_cog(ServiceManager(bot))
