from discord.ext import commands
from permissions import owner
from tabulate import tabulate as tab


class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @owner()
    async def ignore(self, ctx, subject, subject_id):
        try:
            int(subject_id)
        except ValueError:
            raise AttributeError(f"'{subject_id}' is no valid number")

        if subject == "guild":
            guild = self.bot.get_guild(int(subject_id))
            if guild is None:
                raise RuntimeError("Server does not exist.")
            guild_id = guild.id
            if guild_id in self.bot.permit.ignored_guilds:
                raise RuntimeError("Server is already ignored.")
            self.bot.permit.add_ignore("guilds", guild_id)
            await ctx.send(f'Added "{guild.name}" to ignore list. '
                           f'None of the commands from this server will be executed anymore.')

        elif subject == "channel":
            channel = self.bot.get_channel(int(subject_id))
            if channel is None:
                raise RuntimeError("Channel does not exist.")
            channel_id = channel.id
            if channel_id in self.bot.permit.ignored_channels:
                raise RuntimeError("Channel is already ignored.")
            self.bot.permit.add_ignore("channels", channel_id)
            await ctx.send(f'Added "{channel.name}" in "{channel.guild.name}" to ignore list. '
                           f'None of the commands from this channel will be executed anymore.')

        elif subject == "user":
            user = self.bot.get_user(int(subject_id))
            if user is None:
                raise RuntimeError("User does not exist.")
            user_id = user.id
            if user_id in self.bot.permit.ignored_users:
                raise RuntimeError("User is already ignored.")
            self.bot.permit.add_ignore("users", user_id)
            await ctx.send(f'Added "{user.name}" to ignore list. '
                           f'None of the commands from this user will be executed anymore.')

        else:
            raise AttributeError(f"'{subject}' is no valid argument")

    @commands.command()
    @owner()
    async def note(self, ctx, subject, subject_id):
        try:
            int(subject_id)
        except ValueError:
            raise AttributeError(f"'{subject_id}' is no valid number")

        if subject == "guild":
            guild = self.bot.get_guild(int(subject_id))
            if guild is None:
                raise RuntimeError("Server does not exist.")
            guild_id = guild.id
            if guild_id not in self.bot.permit.ignored_guilds:
                raise RuntimeError("Server is not in the ignore list.")
            self.bot.permit.remove_ignore("guilds", guild_id)
            await ctx.send(f'Removed "{guild.name}" from ignore list. '
                           f'Commands from this server are executed again.')

        elif subject == "channel":
            channel = self.bot.get_channel(int(subject_id))
            if channel is None:
                raise RuntimeError("Channel does not exist.")
            channel_id = channel.id
            if channel_id not in self.bot.permit.ignored_channels:
                raise RuntimeError("Channel is not in the ignore list.")
            self.bot.permit.remove_ignore("channels", channel_id)
            await ctx.send(f'Removed "{channel.name}" in "{channel.guild.name}" from ignore list. '
                           f'Commands from this channel are executed again.')

        elif subject == "user":
            user = self.bot.get_user(int(subject_id))
            if user is None:
                raise RuntimeError("User does not exist.")
            user_id = user.id
            if user_id not in self.bot.permit.ignored_users:
                raise RuntimeError("User is not in the ignore list.")
            self.bot.permit.remove_ignore("users", user_id)
            await ctx.send(f'Removed "{user.name}" from ignore list. '
                           f'Commands from this user are executed again.')

        else:
            raise AttributeError(f"'{subject}' is no valid argument")

    @commands.command()
    @owner()
    async def ignored(self, ctx):
        user_headers = ["ID", "Name", "Discriminator"]
        channel_headers = ["ID", "Name", "Server"]
        guild_headers = ["ID", "Name"]
        user_table = []
        channel_table = []
        guild_table = []

        for u in self.bot.permit.ignored_users:
            user = self.bot.get_user(u)
            user_table.append([user.id,
                               user.name,
                               user.discriminator])
        for c in self.bot.permit.ignored_channels:
            channel = self.bot.get_channel(c)
            channel_table.append([channel.id,
                                  channel.name,
                                  channel.guild.name])
        for g in self.bot.permit.ignored_guilds:
            guild = self.bot.get_guild(g)
            guild_table.append([guild.id,
                                guild.name])

        message = "```" \
                  "Currently ignored:\n\n" \
                  "Users:\n" \
                  f"{tab(user_table, headers=user_headers)}\n\n" \
                  "Channels:\n" \
                  f"{tab(channel_table, headers=channel_headers)}\n\n" \
                  f"Servers:\n" \
                  f"{tab(guild_table, headers=guild_headers)}" \
                  "```"

        await ctx.send(message)


def setup(bot):
    bot.add_cog(Permissions(bot))
