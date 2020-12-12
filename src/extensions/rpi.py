from discord.ext import commands
from core.permissions import is_owner
from core.system import measure_temp
from core.database import ConfigManager


class RaspberryPi(commands.Cog, name="Raspberry Pi"):
    def __init__(self, bot):
        self.bot = bot
        self.config: ConfigManager = self.bot.config

    @commands.command()
    @commands.check(is_owner)
    async def temp(self, ctx):
        """
        Displays the cpu temperature.
        """
        try:
            temp = measure_temp()
        except ValueError:
            await ctx.send("This command is not available on this system.")
        else:
            await ctx.send(f'{temp} °C')


def setup(bot):
    bot.add_cog(RaspberryPi(bot))
