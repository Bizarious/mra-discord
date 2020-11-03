from discord.ext import commands
from core.permissions import owner
from tabulate import tabulate as tab
from core.database import Data, ConfigManager


class BlackList(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.permission_needed = ["ignored_users",
                                  "ignored_guilds",
                                  "ignored_channels",
                                  "blacklist"]
        self.data: Data = self.bot.data
        self.config: ConfigManager = self.bot.config
        self.permissions = self.data.get_json(file="blacklist")
        self.first_startup()

    def first_startup(self):
        changed = False
        for s in self.permission_needed:
            if s not in self.permissions.keys():
                changed = True
                self.permissions[s] = []
        if changed:
            self.data.set_json(file="blacklist", data=self.permissions)

    @property
    def bot_owner(self):
        return int(self.config.get_config("botOwner"))

    @property
    def ignored_users(self):
        return self.permissions["ignored_users"]

    @property
    def ignored_guilds(self):
        return self.permissions["ignored_guilds"]

    @property
    def ignored_channels(self):
        return self.permissions["ignored_channels"]

    @property
    def blacklist(self):
        return self.permissions["blacklist"]

    def add_ignore(self, subject, subject_id):
        real_subject = f"ignored_{subject}"
        self.permissions[real_subject].append(subject_id)
        self.data.set_json(file="blacklist", data=self.permissions)

    def remove_ignore(self, subject, subject_id):
        real_subject = f"ignored_{subject}"
        self.permissions[real_subject].remove(subject_id)
        self.data.set_json(file="blacklist", data=self.permissions)

    def check_ignored(self, message):
        a_id = message.author.id
        c = message.channel
        g = message.guild
        if self.bot_owner == a_id:
            return True
        if a_id not in self.ignored_users:
            if g is not None:
                if g.id not in self.ignored_guilds and \
                        c.id not in self.ignored_channels:
                    return True
        return False

    @commands.command()
    @owner()
    async def ignore(self, ctx, subject, subject_id):
        """
        Adds entity to the ignore list.
        """
        try:
            int(subject_id)
        except ValueError:
            raise AttributeError(f"'{subject_id}' is no valid number")

        if subject == "guild":
            guild = self.bot.get_guild(int(subject_id))
            if guild is None:
                raise RuntimeError("Server does not exist.")
            guild_id = guild.id
            if guild_id in self.ignored_guilds:
                raise RuntimeError("Server is already ignored.")
            self.add_ignore("guilds", guild_id)
            await ctx.send(f'Added "{guild.name}" to ignore list. '
                           f'None of the commands from this server will be executed anymore.')

        elif subject == "channel":
            channel = self.bot.get_channel(int(subject_id))
            if channel is None:
                raise RuntimeError("Channel does not exist.")
            channel_id = channel.id
            if channel_id in self.ignored_channels:
                raise RuntimeError("Channel is already ignored.")
            self.add_ignore("channels", channel_id)
            await ctx.send(f'Added "{channel.name}" in "{channel.guild.name}" to ignore list. '
                           f'None of the commands from this channel will be executed anymore.')

        elif subject == "user":
            user = self.bot.get_user(int(subject_id))
            if user is None:
                raise RuntimeError("User does not exist.")
            user_id = user.id
            if user_id in self.ignored_users:
                raise RuntimeError("User is already ignored.")
            self.add_ignore("users", user_id)
            await ctx.send(f'Added "{user.name}" to ignore list. '
                           f'None of the commands from this user will be executed anymore.')

        else:
            raise AttributeError(f"'{subject}' is no valid argument")

    @commands.command()
    @owner()
    async def note(self, ctx, subject, subject_id):
        """
        Removes entities from the ignore list.
        """
        try:
            int(subject_id)
        except ValueError:
            raise AttributeError(f"'{subject_id}' is no valid number")

        if subject == "guild":
            guild = self.bot.get_guild(int(subject_id))
            if guild is None:
                raise RuntimeError("Server does not exist.")
            guild_id = guild.id
            if guild_id not in self.ignored_guilds:
                raise RuntimeError("Server is not in the ignore list.")
            self.remove_ignore("guilds", guild_id)
            await ctx.send(f'Removed "{guild.name}" from ignore list. '
                           f'Commands from this server are executed again.')

        elif subject == "channel":
            channel = self.bot.get_channel(int(subject_id))
            if channel is None:
                raise RuntimeError("Channel does not exist.")
            channel_id = channel.id
            if channel_id not in self.ignored_channels:
                raise RuntimeError("Channel is not in the ignore list.")
            self.remove_ignore("channels", channel_id)
            await ctx.send(f'Removed "{channel.name}" in "{channel.guild.name}" from ignore list. '
                           f'Commands from this channel are executed again.')

        elif subject == "user":
            user = self.bot.get_user(int(subject_id))
            if user is None:
                raise RuntimeError("User does not exist.")
            user_id = user.id
            if user_id not in self.ignored_users:
                raise RuntimeError("User is not in the ignore list.")
            self.remove_ignore("users", user_id)
            await ctx.send(f'Removed "{user.name}" from ignore list. '
                           f'Commands from this user are executed again.')

        else:
            raise AttributeError(f"'{subject}' is no valid argument")

    @commands.command()
    @owner()
    async def ignored(self, ctx):
        """
        Shows all ignored entities.
        """
        user_headers = ["ID", "Name", "Discriminator"]
        channel_headers = ["ID", "Name", "Server"]
        guild_headers = ["ID", "Name"]
        user_table = []
        channel_table = []
        guild_table = []

        for u in self.ignored_users:
            user = self.bot.get_user(u)
            user_table.append([user.id,
                               user.name,
                               user.discriminator])
        for c in self.ignored_channels:
            channel = self.bot.get_channel(c)
            channel_table.append([channel.id,
                                  channel.name,
                                  channel.guild.name])
        for g in self.ignored_guilds:
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

    def on_message_check(self, message):
        return self.check_ignored(message)


def setup(bot):
    bot.add_cog(BlackList(bot))
