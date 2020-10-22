from discord.ext import commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def task(self, ctx, date_string, *, message):
        self.bot.ipc.send(dst="task", cmd="task", task="Reminder", author=ctx.message.author.id,
                          channel=ctx.message.channel.id,
                          message=message, date_string=date_string)


def setup(bot):
    bot.add_cog(Tasks(bot))
