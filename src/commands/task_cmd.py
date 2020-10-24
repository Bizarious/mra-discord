from discord.ext import commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def task(self, ctx, date_string, *, message):
        t = self.bot.ipc.pack(author_id=ctx.message.author.id, channel_id=ctx.message.channel.id, message=message,
                              date_string=date_string)
        self.bot.ipc.send(dst="task", package=t, cmd="task", task="Reminder", author_id=ctx.message.author.id)


def setup(bot):
    bot.add_cog(Tasks(bot))
