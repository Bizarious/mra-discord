from discord.ext import commands
from permissions import is_it_me


class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @is_it_me()
    async def ignore(self, ctx, subject, *, name):
        if subject == "guild":
            guild_id = self.bot.get_guild_id(name)
            if guild_id in self.bot.permit.guilds:
                raise RuntimeError("Server is already ignored.")
            self.bot.permit.add_ignore("guilds", guild_id)
            await ctx.send(f'Added "{name}" to ignore list. '
                           f'None of the commands from this server will be executed anymore.')
        elif subject == "channel":
            name = name.split("$")
            channel_id = self.bot.get_channel_id(name[0], name[1])
            if channel_id in self.bot.permit.channels:
                raise RuntimeError("Channel is already ignored.")
            self.bot.permit.add_ignore("channels", channel_id)
            await ctx.send(f'Added "{name[1]}" in "{name[0]}" to ignore list. '
                           f'None of the commands from this channel will be executed anymore.')
        elif subject == "user":
            user_id = self.bot.get_user_id(name)
            if user_id in self.bot.permit.users:
                raise RuntimeError("User is already ignored.")
            self.bot.permit.add_ignore("users", user_id)
            await ctx.send(f'Added "{name}" to ignore list. '
                           f'None of the commands from this user will be executed anymore.')

    @commands.command()
    @is_it_me()
    async def attention(self, ctx, subject, *, name):
        if subject == "guild":
            guild_id = self.bot.get_guild_id(name)
            if guild_id not in self.bot.permit.guilds:
                raise RuntimeError("Server is not in the ignore list.")
            self.bot.permit.remove_ignore("guilds", guild_id)
            await ctx.send(f'Removed "{name}" from ignore list. '
                           f'Commands from this server are executed again.')
        elif subject == "channel":
            name = name.split("$")
            channel_id = self.bot.get_channel_id(name[0], name[1])
            if channel_id not in self.bot.permit.channels:
                raise RuntimeError("Channel is not in the ignore list.")
            self.bot.permit.remove_ignore("channels", channel_id)
            await ctx.send(f'Removed "{name[1]}" in "{name[0]}" from ignore list. '
                           f'Commands from this channel are executed again.')
        elif subject == "user":
            user_id = self.bot.get_user_id(name)
            if user_id not in self.bot.permit.users:
                raise RuntimeError("User is not in the ignore list.")
            self.bot.permit.remove_ignore("users", user_id)
            await ctx.send(f'Removed "{name}" from ignore list. '
                           f'Commands from this user are executed again.')

    @commands.command()
    @is_it_me()
    async def ignored(self, ctx):
        void = "  "
        message = f"```Currently ignored:\n\n" \
                  f"Servers:\n"
        for s in self.bot.permit.guilds:
            message += void
            message += self.bot.get_guild(s).name
            message += "\n"
        message += "Channels:\n"
        for c in self.bot.permit.channels:
            message += void
            channel = self.bot.get_channel(c)
            message += f'{channel.name}/{channel.guild.name}'
            message += "\n"
        message += "Users:\n"
        for u in self.bot.permit.users:
            message += void
            message += self.bot.get_user(u).name
            message += "\n"
        message += "```"
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Permissions(bot))
