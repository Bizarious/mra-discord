from discord.ext import commands
from core.permissions import is_owner
from tabulate import tabulate as tab
from core.database import Data, ConfigManager
from typing import Union


class BlackList(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.permission_needed = ["ignored_users",
                                  "ignored_guilds",
                                  "ignored_channels",
                                  "ignored_dms",
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
    def bot_owner(self) -> int:
        return int(self.config.get_config("botOwner"))

    @property
    def ignored_users(self) -> list:
        return self.permissions["ignored_users"]

    @property
    def ignored_guilds(self) -> list:
        return self.permissions["ignored_guilds"]

    @property
    def ignored_channels(self) -> list:
        return self.permissions["ignored_channels"]

    @property
    def ignored_dms(self) -> list:
        return self.permissions["ignored_dms"]

    @property
    def blacklist(self) -> list:
        return self.permissions["blacklist"]

    def add_ignore(self, subject: str, subject_id: Union[str, int]):
        real_subject = f"ignored_{subject}"
        if subject_id in self.permissions[real_subject]:
            raise ValueError(subject_id)
        self.permissions[real_subject].append(subject_id)
        self.data.set_json(file="blacklist", data=self.permissions)

    def remove_ignore(self, subject: str, subject_id: Union[str, int]):
        real_subject = f"ignored_{subject}"
        if subject_id == "every":
            if real_subject not in self.permissions.keys():
                raise KeyError(real_subject)
            self.permissions[real_subject] = []
        else:
            self.permissions[real_subject].remove(subject_id)
        self.data.set_json(file="blacklist", data=self.permissions)

    def check_ignored(self, message) -> bool:
        a_id = message.author.id
        c = message.channel
        g = message.guild
        if self.bot_owner == a_id:
            return True
        if a_id not in self.ignored_users and "all" not in self.ignored_users:
            if g is not None:
                if g.id not in self.ignored_guilds and \
                        c.id not in self.ignored_channels and \
                        "all" not in self.ignored_guilds and \
                        "all" not in self.ignored_channels:
                    return True
            else:
                if "all" in self.ignored_dms:
                    return False
                return True
        return False

    @commands.command()
    @commands.check(is_owner)
    async def ignore(self, ctx, subject, subject_id):
        """
        Adds an subject to the ignore list.

        subject:

            guild
            channel
            user
            all:
                Ignores all subjects of the given type.


        subject_id:

            The id of the subject.

            When using 'all' as subject, this can be:
                guilds
                channels
                users
                dms

            Else:

                The id as number of the subject.
        """
        if subject in ["guild", "channel", "user"]:
            try:
                int(subject_id)
            except ValueError:
                raise RuntimeError(f"'{subject_id}' is no valid number.")

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

        elif subject == "all":
            try:
                self.add_ignore(subject_id, subject)
            except KeyError:
                raise RuntimeError(f"'{subject_id}' is no valid argument.")
            except ValueError:
                raise RuntimeError(f"'{subject}' is already part of the '{subject_id}' ignore list.")
            await ctx.send(f"All {subject_id} will be ignored now.")

        else:
            raise RuntimeError(f"'{subject}' is no valid argument.")

    @commands.command()
    @commands.check(is_owner)
    async def note(self, ctx, subject, subject_id):
        """
        Removes an subject from the ignore list.

        subject:

            guild
            channel
            user
            all:
                Removes the 'all' modifier of the given subject.
                Subjects that were added by id previously will NOT be removed. If that is your goal,
                use 'every' instead.

            every:
                Removes every subject of the given type from the ignore list.

        subject_id:

            The id of the subject.

            When using 'all' as subject:
                guilds
                channels
                users
                dms

            When using 'every' as subject:
                guild
                channel
                user

            Else:
                The id as number of the subject.
        """
        if subject in ["guild", "channel", "user"]:
            try:
                int(subject_id)
            except ValueError:
                raise RuntimeError(f"'{subject_id}' is no valid number.")

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

        elif subject == "all":
            try:
                self.remove_ignore(subject_id, subject)
            except KeyError:
                raise RuntimeError(f"'{subject_id}' is no valid argument.")
            await ctx.send(f"{subject_id} will not be ignored anymore.")

        elif subject == "every":
            try:
                self.remove_ignore(subject_id + "s", subject)
            except KeyError:
                raise RuntimeError(f"'{subject_id}' is no valid argument.")
            await ctx.send(f"Every {subject_id} was removed from the ignore list.")

        else:
            raise RuntimeError(f"'{subject}' is no valid argument.")

    @commands.command()
    @commands.check(is_owner)
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

        if "all" not in self.ignored_users:
            for u in self.ignored_users:
                user = self.bot.get_user(u)
                user_table.append([user.id,
                                   user.name,
                                   user.discriminator])
        else:
            user_table = [["all", "all", "all"]]

        if "all" not in self.ignored_channels:
            for c in self.ignored_channels:
                channel = self.bot.get_channel(c)
                channel_table.append([channel.id,
                                      channel.name,
                                      channel.guild.name])
        else:
            channel_table = [["all", "all", "all"]]

        if "all" not in self.ignored_guilds:
            for g in self.ignored_guilds:
                guild = self.bot.get_guild(g)
                guild_table.append([guild.id,
                                    guild.name])
        else:
            guild_table = [["all", "all"]]

        if "all" in self.ignored_dms:
            dms = "Yes"
        else:
            dms = "No"

        message = "```" \
                  "Currently ignored:\n\n" \
                  "Users:\n" \
                  f"{tab(user_table, headers=user_headers)}\n\n" \
                  "Channels:\n" \
                  f"{tab(channel_table, headers=channel_headers)}\n\n" \
                  f"Servers:\n" \
                  f"{tab(guild_table, headers=guild_headers)}\n\n" \
                  f"Direct Messages: {dms}" \
                  "```"

        await ctx.send(message)

    def on_message_check(self, message) -> bool:
        return self.check_ignored(message)


def setup(bot):
    bot.add_cog(BlackList(bot))
