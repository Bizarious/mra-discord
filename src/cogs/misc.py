from discord import DMChannel
from discord.ext import commands
import random
import asyncio
from core.version import __version__


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, content):
        """
        Echos the given text back to the channel.
        """
        await ctx.send(content)

    @commands.command()
    async def clear(self, ctx, n=5, mode=None):
        """
        Clears a given amount of messages in the channel.

        Mode:
            Leave it clean, when you want to purge commands and bot messages only.
            Write 'all' for deleting all messages, regardless of the author. This does not work with direct messages.
        """

        def message_check(m):
            if m.author == self.bot.user or m.content.startswith(self.bot.prefixes[str(ctx.message.guild.id)]):
                return True
            return False

        if not isinstance(ctx.channel, DMChannel):
            if mode is None:
                await ctx.channel.purge(limit=n, check=message_check)
            elif mode == "all":
                await ctx.channel.purge(limit=n)
        else:
            async for message in ctx.author.dm_channel.history(limit=n):
                if message.author == self.bot.user:
                    await message.delete()
                    await asyncio.sleep(0.2)

    @commands.command("rmdme")
    async def remind_me(self, ctx, date_string, message, label=None, number=0):
        """
        Adds a reminder-task.

        message:
            The message to display.

        label:
            Sets a label for this task for easier recognition. If not specified the label will be the message.

        Run 'help tasks' to get more information.
        """
        try:
            int(number)
        except ValueError:
            raise AttributeError(f"'{number}' is no valid number")
        if label is None:
            label = message
        t = self.bot.ipc.pack(author_id=ctx.message.author.id,
                              channel_id=ctx.message.channel.id,
                              message=message,
                              date_string=date_string,
                              label=label,
                              number=int(number)
                              )
        self.bot.ipc.send(dst="task",
                          package=t, cmd="task",
                          task="Reminder",
                          author_id=ctx.message.author.id,
                          channel_id=ctx.message.channel.id
                          )

    @commands.command()
    async def version(self, ctx):
        await ctx.send(__version__)

    @commands.command()
    async def choose(self, ctx, amount=0):
        """
        Chooses randomly a member of the voice-channel you are in and mentions it.
        """
        if amount > 10000:
            raise RuntimeError("Number of rolls must not be greater than 10000.")
        guild = self.bot.get_guild(ctx.message.guild.id)
        vc = guild.voice_channels
        for c in vc:
            for m in c.members:
                if m.id == ctx.message.author.id:
                    if amount == 0:
                        i = random.randint(0, len(c.members) - 1)
                        await ctx.send(c.members[i].mention)
                        return
                    else:
                        amount_list = []
                        for _ in range(amount):
                            amount_list.append(random.randint(0, len(c.members) - 1))
                        for i in range(len(c.members)):
                            await ctx.send(c.members[i].mention + f': {amount_list.count(i)}')
                        return

        await ctx.send("You are not in a voice-channel.")


def setup(bot):
    bot.add_cog(Misc(bot))
