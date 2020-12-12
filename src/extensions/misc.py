import discord
import platform as pf
from discord import DMChannel
from discord.ext import commands
import random
import asyncio
from core.version import __version__
from core.enums import Dates
from core.permissions import is_group_member, is_owner


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
    @commands.check_any(commands.check(is_owner),
                        commands.check(is_group_member("task")))
    async def remind_me(self, ctx, date_string, message, message_args="", label=None, number=0):
        """
        Adds a reminder task.

        message:
            The message to display.

        label:
            Sets a label for this task for easier recognition. If not specified the label will be the message.

        Run 'help tasks' to get more information.
        """
        try:
            int(number)
        except ValueError:
            raise RuntimeError(f"'{number}' is no valid number")
        if message_args != "":
            if not is_group_member("taskExtra")(ctx) and not is_owner(ctx):
                raise PermissionError("You are not allowed to use special message arguments.")
        if number != 0 and " " not in date_string:
            if not is_group_member("taskExtra")(ctx) and not is_owner(ctx):
                raise PermissionError("You are not allowed to give a custom number of executions.")

        if label is None:
            label = message
        t = self.bot.ipc.pack(author_id=ctx.message.author.id,
                              channel_id=ctx.message.channel.id,
                              message=message,
                              message_args=message_args,
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
    async def info(self, ctx):
        """
        Displays general information and statistics about the bot.
        """
        py_version = pf.python_version()
        dpy_version = discord.__version__
        server_count = len(self.bot.guilds)
        member_count = len(set(self.bot.get_all_members()))
        system = pf.system()

        start_date = self.bot.start_time.strftime(Dates.DATE_FORMAT.value)

        embed = discord.Embed(color=discord.Colour.blue(),
                              title="Bot Statistics",
                              description=f"General Information about <@{self.bot.user.id}>")

        embed.add_field(name="Bot Owner", value=f"<@{self.bot.permit.bot_owner}>", inline=False)
        embed.add_field(name="Bot Version", value=f"`{__version__}`", inline=False)
        embed.add_field(name="Online since", value=f"{start_date}", inline=False)
        embed.add_field(name="Python Version", value=f"{py_version}", inline=True)
        embed.add_field(name="Discord.py Version", value=f"{dpy_version}", inline=True)
        embed.add_field(name="OS", value=f"{system}", inline=True)
        embed.add_field(name="Observable Users", value=f"{str(member_count)}", inline=True)
        embed.add_field(name="Observable Servers", value=f"{str(server_count)}", inline=True)

        await ctx.send(embed=embed)

    @commands.command("userinfo")
    async def user_info(self, ctx):
        """
        Displays information about the user.
        """
        groups: list = self.bot.permit.member_of(ctx.author.id)
        groups_str = ""
        if not groups:
            groups_str = "-None-"
        for g in groups:
            groups_str += f"{g}, "
        if groups_str != "-None-":
            groups_str = groups_str[:-2]

        embed = discord.Embed(color=discord.Colour.blue(),
                              title=f"User Statistics",
                              description=f"General Information about <@{ctx.author.id}>")
        if ctx.author.id == self.bot.permit.bot_owner:
            embed.add_field(name="Bot Owner", value="`You are the bot owner`", inline=False)
        embed.add_field(name="Groups you are member of", value=f"{groups_str}", inline=False)

        await ctx.send(embed=embed)

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

        await ctx.send("You are not in a voice channel.")

    @commands.command("listcogs")
    async def list_cogs(self, ctx):
        """
        Lists all existing cogs.
        """
        result = "```\n"
        for c in self.bot.cogs.keys():
            result += f"{c}\n"
        result += "```"
        await ctx.send(result)


def setup(bot):
    bot.add_cog(Misc(bot))
