from discord.ext import commands
from tabulate import tabulate as tab
from core.permissions import is_owner, is_it_me


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.permit.add_group("task", True)

    @commands.command()
    async def gt(self, ctx, a_id=None):
        """
        Displays all active tasks.

        a_id:
            The id of the user. Leave it empty or set your id, to get your own messages.
            Set 0 to get system tasks.
        """
        author_id = ctx.author.id
        if a_id is not None:
            if not is_it_me(ctx, int(a_id)) and not is_owner(ctx):
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
        headers = ["ID", "Type", "Label", "Creation Date", "Next Execution Date"]
        table = []
        for i in range(len(tasks)):
            table.append([i+1,
                          tasks[i]["extra"]["type"],
                          tasks[i]["extra"]["label"],
                          tasks[i]["extra"]["creation_time"],
                          tasks[i]["extra"]["next_time"]])
        await ctx.send(f"```{tab(table, headers=headers)}```")

    @commands.command("dt")
    async def delete_task(self, ctx, task_id, a_id=None):
        """
        Deletes a message.

        task_id:
            The id of the task that shall be deleted. Get ids with 'gt'.

        a_id:
            The id of the user. Leave it empty or set your id, to delete your own messages.
            Set 0 to delete system tasks.
        """
        author_id = ctx.author.id
        if a_id is not None:
            if not is_it_me(ctx, int(a_id)) and not is_owner(ctx):
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

    @commands.command("tasks", hidden=True)
    async def task_help(self, _):
        """
        General help for task creating.

        date_string:

            Possibility 1:
                Can be of the form 'xh', 'xm', 'xs' or every combination of them, with x being a
                number and h, m and s being hours, minutes and seconds respectively.

            Possibility 2: Can be a cronjob like string of the form "* * * * *", with the stars being
                minutes, hours, days, months and weekdays respectively.

        label:
            Sets a label for this task for easier recognition.

        number:
            Number of times the task shall be executed.
            -1: Infinite amount of times
            > 0: Finite amount of times
            0: Default value:
                1 for date strings like '1h'
                -1 for cronjob like date strings

        """
        pass


def setup(bot):
    bot.add_cog(Tasks(bot))
