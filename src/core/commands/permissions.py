from discord.ext import commands
from core.permissions import Permissions, is_owner
from core.permissions.errors import GroupUserException


class PermissionsHandler(commands.Cog, name="Permissions Handler"):
    def __init__(self, bot):
        self.bot = bot
        self.permissions: Permissions = self.bot.permit

    def check_default_users(self, uid: int):
        self.permissions.add_to_default_groups(uid)

    @commands.command("autg")
    @commands.check(is_owner)
    async def add_user_to_group(self, ctx, uid, group):
        try:
            int(uid)
        except ValueError:
            raise AttributeError(f"'{uid}' is no valid number.")
        if int(uid) not in self.permissions.known_users:
            raise GroupUserException(f"The user of the id '{uid}' is not known.")
        if int(uid) == ctx.author.id:
            raise GroupUserException(f"You cannot add yourself to a group.")

        self.permissions.add_to_group(int(uid), group)
        await ctx.send(f"Added <@{uid}> to '{group}'.")

    @commands.command("rufg")
    async def remove_user_from_group(self, ctx, uid, group):
        try:
            int(uid)
        except ValueError:
            raise AttributeError(f"'{uid}' is no valid number.")
        if int(uid) not in self.permissions.known_users:
            raise GroupUserException(f"The user of the id '{uid}' is not known.")
        if int(uid) == ctx.author.id:
            raise GroupUserException(f"You cannot remove yourself from a group.")

        self.permissions.remove_from_group(int(uid), group)
        await ctx.send(f"Removed <@{uid}> from '{group}'.")

    @commands.Cog.listener()
    async def on_ready(self):
        users = self.bot.users
        for u in users:
            if u != self.bot.user:
                self.permissions.add_to_default_groups(u.id)

    @commands.Cog.listener()
    async def on_member_join(self, user):
        self.permissions.add_to_default_groups(user.id)


def setup(bot):
    bot.add_cog(PermissionsHandler(bot))
