from typing import TYPE_CHECKING
from enum import Enum
from nextcord.ext import commands

if TYPE_CHECKING:
    from .data import DataProvider
    from .data import DataDict


class Rank(Enum):
    OWNER = 3
    ADMIN = 2
    MODERATOR = 1
    USER = 0


class Permissions:

    def __init__(self, data_provider: "DataProvider"):
        self._data_provider = data_provider
        self._permissions_dict: DataDict = self._data_provider.get_json_data(
            "permissions.json",
            {"owner": 0, "admin": [], "moderator": []}
        )

    def is_owner(self, user_id: int) -> bool:
        return self._permissions_dict["owner"] == user_id

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._permissions_dict["admin"]

    def is_moderator(self, user_id: int) -> bool:
        return user_id in self._permissions_dict["moderator"]

    def is_admin_or_higher(self, user_id: int) -> bool:
        return self.is_admin(user_id) or self.is_owner(user_id)

    def is_moderator_or_higher(self, user_id: int) -> bool:
        return self.is_admin_or_higher(user_id) or self.is_moderator(user_id)

    def get_rank(self, user_id: int) -> str:
        if self.is_owner(user_id):
            return "owner"
        if self.is_admin(user_id):
            return "admin"
        if self.is_moderator(user_id):
            return "moderator"
        else:
            return "user"


def owner():
    async def predicate(ctx):
        return ctx.bot.permissions.is_owner(ctx.author.id)
    return commands.check(predicate)


def admin():
    async def predicate(ctx):
        return ctx.bot.permissions.is_admin_or_higher(ctx.author.id)
    return commands.check(predicate)


def moderator():
    async def predicate(ctx):
        return ctx.bot.permissions.is_moderator_or_higher(ctx.author.id)
    return commands.check(predicate)
