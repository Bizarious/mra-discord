from discord.ext import commands
from core.permissions import Permissions, is_owner
from core.permissions.errors import GroupUserException


class PermissionsHandler(commands.Cog, name="Permissions Handler"):
    def __init__(self, bot):
        self.bot = bot
        self.permissions: Permissions = self.bot.permit

    def check_default_users(self, uid: int):
        self.permissions.add_to_default_groups(uid)

    @commands.command("autg", hidden=True)
    @commands.check(is_owner)
    async def add_user_to_group(self, ctx, uid, group):
        """
        Adds a user to a group.

        uid:

            The users id.

        group:

            The group name.
        """
        try:
            int(uid)
        except ValueError:
            raise RuntimeError(f"'{uid}' is no valid number.")
        if int(uid) not in self.permissions.known_users:
            raise GroupUserException(f"The user of the id '{uid}' is not known.")
        if int(uid) == ctx.author.id and not is_owner(ctx):
            raise GroupUserException(f"You cannot add yourself to a group.")

        self.permissions.add_to_group(int(uid), group)
        await ctx.send(f"Added <@{uid}> to '{group}'.")

    @commands.command("rufg", hidden=True)
    @commands.check(is_owner)
    async def remove_user_from_group(self, ctx, uid, group):
        """
        Removes a user from a group.

        uid:

            The users id.

        group:

            The group name.
        """
        try:
            int(uid)
        except ValueError:
            raise RuntimeError(f"'{uid}' is no valid number.")
        if int(uid) not in self.permissions.known_users:
            raise GroupUserException(f"The user of the id '{uid}' is not known.")
        if int(uid) == ctx.author.id and not is_owner(ctx):
            raise GroupUserException(f"You cannot remove yourself from a group.")

        self.permissions.remove_from_group(int(uid), group)
        await ctx.send(f"Removed <@{uid}> from '{group}'.")

    @commands.command("deluser", hidden=True)
    @commands.check(is_owner)
    async def delete_user(self, ctx, uid):
        """
        Removes a user from all groups and the list of known users.

        uid:

            The users id.
        """
        try:
            int(uid)
        except ValueError:
            raise RuntimeError(f"'{uid}' is no valid number.")

        self.permissions.delete_user(int(uid))
        await ctx.send(f"Removed <@{uid}> from all groups.")

    @commands.command("resetperm", hidden=True)
    @commands.check(is_owner)
    async def delete_all_users(self, ctx):
        """
        Removes all users. Serves as a 'reset' of the permissions state.
        """
        self.permissions.delete_all_users()
        await ctx.send("Removed all users from the permissions.")

    @commands.command("adu", hidden=True)
    @commands.check(is_owner)
    async def set_default_permissions(self, ctx):
        """
        Discovers unknown users and adds them to the default groups.
        """
        users = [u.id for u in self.bot.users if u != self.bot.user]
        counter = self.permissions.add_to_default_groups(*users)
        await ctx.send(f"```Added {counter} new users to the default groups.```")

    @commands.command("showgr", hidden=True)
    @commands.check(is_owner)
    async def get_groups(self, ctx):
        """
        Displays all available groups.
        """
        groups = self.permissions.groups.keys()
        result = "```Available groups:\n\n"
        for g in groups:
            result += f"{g}\n"
        result += "```"

        await ctx.send(result)

    @commands.command("setowner", hidden=True)
    @commands.check(is_owner)
    async def set_bot_owner(self, ctx, uid):
        """
        Sets the bot owner.
        """
        if int(uid) not in self.permissions.known_users:
            raise RuntimeError("This user is not known.")
        self.permissions.bot_owner = uid
        await ctx.send(f"Congratulations <@{uid}>, you are now the owner of this bot.")

    @commands.Cog.listener()
    async def on_ready(self):
        users = [u.id for u in self.bot.users if u != self.bot.user]
        self.permissions.add_to_default_groups(*users)

    @commands.Cog.listener()
    async def on_member_join(self, user):
        self.permissions.add_to_default_groups(user.id)


def setup(bot):
    bot.add_cog(PermissionsHandler(bot))
