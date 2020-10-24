from discord.ext import commands
from tabulate import tabulate as tab


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def task(self, ctx, date_string, *, message):
        t = self.bot.ipc.pack(author_id=ctx.message.author.id,
                              channel_id=ctx.message.channel.id,
                              message=message,
                              date_string=date_string)
        self.bot.ipc.send(dst="task",
                          package=t, cmd="task",
                          task="Reminder",
                          author_id=ctx.message.author.id)

    @commands.command()
    async def gt(self, ctx):
        t = self.bot.ipc.pack()
        pipe = self.bot.ipc.send(dst="task",
                                 create_pipe=True,
                                 package=t, cmd="get_tasks",
                                 author_id=ctx.author.id)
        tasks: list = pipe.recv()
        if tasks is None:
            await ctx.send("You have no active tasks")
            return
        headers = ["ID", "Type", "Creation Date", "Next Execution Date"]
        table = []
        for i in range(len(tasks)):
            table.append([i+1,
                          tasks[i]["extra"]["type"],
                          tasks[i]["extra"]["creation_time"],
                          tasks[i]["extra"]["next_time"]])
        await ctx.send(f"```{tab(table, headers=headers)}```")

    @commands.command("dt")
    async def delete_task(self, ctx, task_id):
        t = self.bot.ipc.pack()
        pipe = self.bot.ipc.send(dst="task",
                                 create_pipe=True,
                                 package=t,
                                 cmd="del_task",
                                 author_id=ctx.author.id,
                                 task_id=task_id)
        answer = pipe.recv()
        if answer is not None:
            await ctx.send(answer)


def setup(bot):
    bot.add_cog(Tasks(bot))
