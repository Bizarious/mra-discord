from discord.ext import commands
from tabulate import tabulate as tab
from permissions import owner_check, is_it_me


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
                          author_id=ctx.message.author.id,
                          channel_id=ctx.message.channel.id)

    @commands.command()
    async def gt(self, ctx, a_id=None):
        author_id = ctx.author.id
        if a_id is not None:
            if not is_it_me(ctx, int(a_id)) and not owner_check(ctx):
                raise commands.CheckFailure()
            author_id = int(a_id)
        t = self.bot.ipc.pack()
        pipe = self.bot.ipc.send(dst="task",
                                 create_pipe=True,
                                 package=t, cmd="get_tasks",
                                 author_id=author_id)
        tasks = pipe.recv()
        if isinstance(tasks, Exception):
            raise tasks
        headers = ["ID", "Type", "Creation Date", "Next Execution Date"]
        table = []
        for i in range(len(tasks)):
            table.append([i+1,
                          tasks[i]["extra"]["type"],
                          tasks[i]["extra"]["creation_time"],
                          tasks[i]["extra"]["next_time"]])
        await ctx.send(f"```{tab(table, headers=headers)}```")

    @commands.command("dt")
    async def delete_task(self, ctx, task_id, a_id=None):
        author_id = ctx.author.id
        if a_id is not None:
            if not is_it_me(ctx, int(a_id)) and not owner_check(ctx):
                raise commands.CheckFailure()
            author_id = int(a_id)
        t = self.bot.ipc.pack()
        pipe = self.bot.ipc.send(dst="task",
                                 create_pipe=True,
                                 package=t,
                                 cmd="del_task",
                                 author_id=author_id,
                                 task_id=task_id)
        answer = pipe.recv()
        if isinstance(answer, Exception):
            raise answer


def setup(bot):
    bot.add_cog(Tasks(bot))
