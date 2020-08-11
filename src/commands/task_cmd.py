from discord.ext import commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def task(self, ctx):
        self.bot.send(dst="task", task="Reminder", author=ctx.message.author.id, channel=ctx.message.channel.id)


def setup(bot):
    bot.add_cog(Tasks(bot))
