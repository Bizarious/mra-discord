import os
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
    async def ignore(self, ctx, subject, *, name):
        if subject == "guild":
            guild_id = self.bot.get_guild_id(name)
            self.bot.permit.add_ignore("guilds", guild_id)
            await ctx.send(f'Added "{name}" to ignore list. '
                           f'None of the commands from this server will be executed anymore.')
        elif subject == "channel":
            name = name.split("$")
            channel_id = self.bot.get_channel_id(name[0], name[1])
            self.bot.permit.add_ignore("channels", channel_id)
            await ctx.send(f'Added "{name[1]}" in "{name[0]}" to ignore list. '
                           f'None of the commands from this channel will be executed anymore.')
        elif subject == "user":
            user_id = self.bot.get_user_id(name)
            self.bot.permit.add_ignore("users", user_id)
            await ctx.send(f'Added "{name}" to ignore list. '
                           f'None of the commands from this user will be executed anymore.')

    @commands.command()
    @is_it_me()
    async def update(self, ctx):
        status = os.popen("git pull --ff-only").read()
        await ctx.send(status)

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

    @commands.command("ignore-status")
    @is_it_me()
    async def ignore_status(self, ctx):
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

    @commands.command("prefix")
    @is_it_me()
    async def change_prefix(self, ctx, prefix):
        self.bot.change_prefix(prefix, ctx.message.guild.id)
        await ctx.send(f'Changed prefix for server "{self.bot.get_guild(ctx.message.guild.id).name}" to "{prefix}"')


def setup(bot):
    bot.add_cog(System(bot))