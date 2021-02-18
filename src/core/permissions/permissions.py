from core.database import Data, ConfigManager
from typing import Union
from enum import Enum


class Rank(Enum):
    USER = 0
    MOD = 1
    ADMIN = 2
    OWNER = 3


class Permissions:
    """
    Represents the permission handling.
    """

    def __init__(self, data, config):
        self.config: ConfigManager = config
        self.data: Data = data
        self.permissions = self.data.get_json(file="permissions")
        self.first_startup()

    def first_startup(self):
        for i in ["ranks", "rules"]:
            if i not in self.permissions.keys():
                self.permissions[i] = {}

        # sets bot owner
        if str(self.bot_owner) not in self.ranks.keys():
            self.ranks[str(self.bot_owner)] = Rank.OWNER.value
        self.data.set_json(file="permissions", data=self.permissions)

    @property
    def bot_owner(self) -> int:
        return int(self.config.get_config("botOwner", "General"))

    @bot_owner.setter
    def bot_owner(self, uid: int):
        del self.ranks[str(self.bot_owner)]
        self.ranks[str(uid)] = Rank.OWNER.value
        self.config.set_config("botOwner", "General", str(uid))

    @property
    def ranks(self) -> dict:
        return self.permissions["ranks"]

    @property
    def rules(self) -> dict:
        return self.permissions["rules"]

    def get_rank_id(self, user_id: int) -> int:
        if str(user_id) not in self.ranks.keys():
            return 0
        return self.ranks[str(user_id)]

    def get_rank(self, user_id: int) -> Rank:
        i = self.get_rank_id(user_id)
        return Rank(i)

    def set_rank(self, user_id: int, rank: Rank):
        self.ranks[str(user_id)] = rank.value
        self.data.set_json(file="permissions", data=self.permissions)

    def allow(self, user_id: int, cmd_name: str):
        """
        Explicitly allows a user to use a command.
        """
        if cmd_name not in self.rules.keys():
            self.rules[cmd_name] = []
        if [user_id, False] in self.rules[cmd_name]:
            self.rules[cmd_name].remove([user_id, False])
        if [user_id, True] not in self.rules[cmd_name]:
            self.rules[cmd_name].append([user_id, True])

        self.data.set_json(file="permissions", data=self.permissions)

    def deny(self, user_id: int, cmd_name: str):
        """
        Explicitly denies a user to use a command.
        """
        if cmd_name not in self.rules.keys():
            self.rules[cmd_name] = []
        if [user_id, True] in self.rules[cmd_name]:
            self.rules[cmd_name].remove([user_id, True])
        if [user_id, False] not in self.rules[cmd_name]:
            self.rules[cmd_name].append([user_id, False])

        self.data.set_json(file="permissions", data=self.permissions)

    def reset_rule(self, user_id: int, cmd_name: str):
        """
        Removes the command rule for a user.
        """
        if cmd_name in self.rules.keys():
            if [user_id, True] in self.rules[cmd_name]:
                self.rules[cmd_name].remove([user_id, True])
            if [user_id, False] in self.rules[cmd_name]:
                self.rules[cmd_name].remove([user_id, False])

        self.data.set_json(file="permissions", data=self.permissions)

    def get_rule(self, user_id: int, cmd_name: str) -> Union[bool, None]:
        """
        Returns the rule, if one exists.
        """
        if cmd_name in self.rules.keys():
            if [user_id, True] in self.rules[cmd_name]:
                return True
            if [user_id, False] in self.rules[cmd_name]:
                return False
        return None


def is_it_me(ctx, a_id: int) -> bool:
    return ctx.author.id == a_id


def is_owner(ctx) -> bool:
    return ctx.message.author.id == ctx.bot.permit.bot_owner


def is_admin_or_higher(ctx) -> bool:
    """
    Admin checker.
    """
    if ctx.command.parent is not None:
        cmd = f"{ctx.command.parent} {ctx.command.name}"
    else:
        cmd = f"{ctx.command.name}"

    user_id = ctx.author.id
    permit: Permissions = ctx.bot.permit
    rule = permit.get_rule(user_id, cmd)
    if rule is None:
        return permit.get_rank_id(user_id) >= Rank.ADMIN.value
    return rule


def is_mod_or_higher(ctx) -> bool:
    """
    Mod checker.
    """
    if ctx.command.parent is not None:
        cmd = f"{ctx.command.parent} {ctx.command.name}"
    else:
        cmd = f"{ctx.command.name}"

    user_id = ctx.author.id
    permit: Permissions = ctx.bot.permit
    rule = permit.get_rule(user_id, cmd)
    if rule is None:
        return permit.get_rank_id(user_id) >= Rank.MOD.value
    return rule


def is_user_or_higher(ctx) -> bool:
    """
    User checker.
    """
    if ctx.command.parent is not None:
        cmd = f"{ctx.command.parent} {ctx.command.name}"
    else:
        cmd = f"{ctx.command.name}"

    user_id = ctx.author.id
    permit: Permissions = ctx.bot.permit
    rule = permit.get_rule(user_id, cmd)
    if rule is None:
        return permit.get_rank_id(user_id) >= Rank.USER.value
    return rule


if __name__ == "__main__":
    print(Rank["admin".upper()])
