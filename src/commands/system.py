from discord.ext import commands
from permissions import is_it_me


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_it_me()
    async def shutdown(self, _):
        await self.bot.logout()

    @commands.command()
    @is_it_me()
    async def restart(self, _):
        self.bot.restart = True
        await self.bot.logout()

    @commands.command()
    @is_it_me()
    async def ignore(self, ctx, subject, name):
        if subject == "guild":
            guild_id = self.bot.get_guild_id(name)
            self.bot.permit.add_ignore("guilds", guild_id)
            await ctx.send(f'Added {name} to ignore list. '
                           f'None of the commands from this server will be executed anymore.')
        elif subject == "channel":
            channel_id = self.bot.get_channel_id(name)
            self.bot.permit.add_ignore("channels", channel_id)
            await ctx.send(f'Added {name} to ignore list. '
                           f'None of the commands from this channel will be executed anymore.')
        elif subject == "user":
            user_id = self.bot.get_user_id(name)
            self.bot.permit.add_ignore("users", user_id)
            await ctx.send(f'Added {name} to ignore list. '
                           f'None of the commands from this user will be executed anymore.')

    @commands.command()
    @is_it_me()
    async def attention(self, ctx, subject, name):
        if subject == "guild":
            guild_id = self.bot.get_guild_id(name)
            if guild_id not in self.bot.permit.guilds:
                raise RuntimeError("Server is not in the ignore list.")
            self.bot.permit.remove_ignore("guilds", guild_id)
            await ctx.send(f'Removed {name} from ignore list. '
                           f'Commands from this server are executed again.')
        elif subject == "channel":
            channel_id = self.bot.get_channel_id(name)
            if channel_id not in self.bot.permit.channels:
                raise RuntimeError("Channel is not in the ignore list.")
            self.bot.permit.remove_ignore("channels", channel_id)
            await ctx.send(f'Removed {name} from ignore list. '
                           f'Commands from this channel are executed again.')
        elif subject == "user":
            user_id = self.bot.get_user_id(name)
            if user_id not in self.bot.permit.users:
                raise RuntimeError("User is not in the ignore list.")
            self.bot.permit.remove_ignore("users", user_id)
            await ctx.send(f'Removed {name} from ignore list. '
                           f'Commands from this user are executed again.')


def setup(bot):
    bot.add_cog(System(bot))
