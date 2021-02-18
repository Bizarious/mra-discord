from discord.ext import commands
from core.permissions import Permissions, is_owner, is_admin_or_higher, is_it_me, Rank
from core.checks import is_integer


class PermissionsHandler(commands.Cog, name="Permissions Handler"):
    def __init__(self, bot):
        self.bot = bot
        self.permissions: Permissions = self.bot.permit

    @commands.command("set-rank")
    async def set_rank(self, ctx, user_id, rank):
        """
        Sets the rank for a user.

        user_id:

            The users id.

        rank:

            The rank the user shall have. Available are:
                admin
                mod
                user
        """

        is_integer(user_id)
        user_id = int(user_id)
        # if is_it_me(ctx, user_id):
        #     await ctx.send("You cannot set your own rank.")
        #     return

        try:
            rank = Rank[rank.upper()]
        except KeyError:
            await ctx.send(f"The rank '{rank}' does not exist. Please choose one of the following:\n"
                           f"admin\n"
                           f"mod\n"
                           f"user")
            return

        user_rank = self.permissions.get_rank_id(user_id)
        if user_rank <= rank.value:
            await ctx.send(f"You cannot apply a rank that is equal or higher than yours.")
            return

        self.permissions.set_rank(user_id, rank)

    @commands.group("permit-rule")
    async def permit_rule(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand.")

    @permit_rule.command()
    async def allow(self, ctx, user_id, cmd):
        """
        Explicitly allows a user to use a command.

        user_id:

            The users id.

        cmd:

            The command the user shall be allowed to issue.
        """

        is_integer(user_id)
        user_id = int(user_id)
        # if is_it_me(ctx, user_id):
        #     await ctx.send("You cannot allow yourself to use a command.")
        #     return

        command = self.bot.get_command(cmd)
        if command is None:
            await ctx.send(f"The command '{cmd}' does not exist.")
            return

        # if self.permissions.get_rank_id(user_id) >= self.permissions.get_rank_id(ctx.author.id):
        #     await ctx.send("You cannot allow a user to use this command "
        #                    "if the user has the same or higher rank as you.")
        #     return

        self.permissions.allow(user_id, cmd)

    @permit_rule.command()
    @commands.check(is_admin_or_higher)
    async def test2(self, _):
        print("Test 2")

    @commands.command()
    @commands.check(is_admin_or_higher)
    async def test(self, _):
        print("Test")


def setup(bot):
    bot.add_cog(PermissionsHandler(bot))
