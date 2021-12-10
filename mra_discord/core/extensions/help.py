from nextcord import Embed
from nextcord.ext import commands
from core.ext import extension


class CustomHelpCommand(commands.MinimalHelpCommand):

    def get_command_signature(self, command: commands.Command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    def _get_bot_avatar(self):
        return self.context.bot.user.avatar or self.context.bot.user.default_avatar

    async def send_bot_help(self, mapping: dict):
        embed = Embed(title="Bot Commands")
        embed.description = self.context.bot.description
        embed.set_author(name=self.context.bot.user.name, icon_url=self._get_bot_avatar().url)

        for cog, command_set in mapping.items():
            # filters all commands by permission
            # if issuing user has not the permissions, the command will not show up
            filtered = await self.filter_commands(command_set, sort=True)
            # if there are no commands, the cog will not be shown
            if not filtered:
                continue

            name = cog.qualified_name if cog else "No category"
            command_list = " ".join(f"`{self.context.clean_prefix}{command.name}`" for command in filtered)
            value = f"{cog.description}\n{command_list}" if cog and cog.description else command_list

            embed.add_field(name=name, value=value)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = Embed(title=self.get_command_signature(command))
        embed.description = command.help or "..."
        embed.set_author(name=self.context.bot.user.name, icon_url=self._get_bot_avatar().url)

        if isinstance(command, commands.Group):
            filtered = await self.filter_commands(command.commands, sort=True)
            for filtered_command in filtered:
                embed.add_field(name=self.get_command_signature(filtered_command),
                                value=filtered_command.short_doc,
                                inline=False
                                )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = Embed(title=cog.qualified_name)
        embed.description = cog.description
        embed.set_author(name=self.context.bot.user.name, icon_url=self._get_bot_avatar().url)

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for filtered_command in filtered:
            embed.add_field(name=self.get_command_signature(filtered_command),
                            value=filtered_command.short_doc,
                            inline=False
                            )

        await self.get_destination().send(embed=embed)

    send_group_help = send_command_help


@extension
class HelpExtension(commands.Cog, name="Help"):

    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self) -> None:
        self.bot.help__command = self._original_help_command
