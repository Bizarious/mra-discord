from discord.ext import commands
from core.database import Data, ConfigManager


class Permissions:

    def __init__(self, data, config):
        self.config: ConfigManager = config
        self.data: Data = data

    @property
    def bot_owner(self) -> int:
        return int(self.config.get_config("botOwner"))


def is_it_me(ctx, a_id: int) -> bool:
    return ctx.author.id == a_id


def owner_check(ctx) -> bool:
    return ctx.message.author.id == ctx.bot.permit.bot_owner


def owner():
    def decorator(ctx) -> bool:
        return ctx.message.author.id == ctx.bot.permit.bot_owner

    return commands.check(decorator)
