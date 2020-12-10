from core.database import Data, ConfigManager
from core.permissions.errors import GroupException, GroupUserException
from copy import deepcopy as dc
from typing import Union


class Permissions:

    def __init__(self, data, config):
        self.config: ConfigManager = config
        self.data: Data = data
        self.permissions_needed = {"known_users": [],
                                   "groups": {}}
        self.default_groups = []
        self.new_groups = []
        self.permissions = self.data.get_json(file="permissions")

        self.first_startup()

    def first_startup(self):
        changed = False
        for s in self.permissions_needed.keys():
            if s not in self.permissions.keys():
                changed = True
                self.permissions[s] = dc(self.permissions_needed[s])
        if changed:
            self.data.set_json(file="permissions", data=self.permissions)

    def add_group(self, name, default=False):
        if name not in self.groups.keys():
            self.groups[name] = []
            self.new_groups.append(name)
        if default:
            if name not in self.default_groups:
                self.default_groups.append(name)

    @property
    def bot_owner(self) -> int:
        return int(self.config.get_config("botOwner", "General"))

    @bot_owner.setter
    def bot_owner(self, uid: int):
        self.config.set_config("botOwner", "General", str(uid))

    @property
    def known_users(self) -> list:
        return self.permissions["known_users"]

    @known_users.setter
    def known_users(self, value: list):
        self.permissions["known_users"] = value

    @property
    def groups(self) -> dict:
        return self.permissions["groups"]

    def in_group(self, uid: int, group: str) -> bool:
        if not self.group_exists(group):
            raise GroupException(f"Group '{group}' does not exist.")
        return uid in self.get_group_list(group)

    def group_exists(self, group: str) -> bool:
        return group in self.groups.keys()

    def member_of(self, uid: int) -> list:
        if uid not in self.known_users:
            raise GroupUserException("This user is not known.")
        result = []
        for g in self.groups.keys():
            if uid in self.groups[g]:
                result.append(g)
        return result

    def get_group_list(self, name) -> Union[list, None]:
        if name in self.permissions["groups"].keys():
            return self.permissions["groups"][name]
        return None

    def add_to_group(self, uid: int, name: str):
        group: list = self.get_group_list(name)
        if group is not None:
            if uid in group:
                raise GroupUserException("This user is already member in this group.")
            group.append(uid)
        else:
            raise GroupException(f"The group '{name}' does not exist.")
        self.data.set_json(file="permissions", data=self.permissions)

    def remove_from_group(self, uid: int, name: str):
        group: list = self.get_group_list(name)
        if group is not None:
            if uid not in group:
                raise GroupUserException("This user is not member in this group.")
            group.remove(uid)
        else:
            raise GroupException("Group not found")
        self.data.set_json(file="permissions", data=self.permissions)

    def add_to_default_groups(self, *uids: int) -> int:
        counter = 0
        for uid in uids:
            for g in self.default_groups:
                if uid not in self.get_group_list(g) and (g in self.new_groups or uid not in self.known_users):
                    self.add_to_group(uid, g)
                if uid not in self.known_users:
                    self.known_users.append(uid)
                    counter += 1
        self.data.set_json(file="permissions", data=self.permissions)
        self.new_groups = []
        return counter

    def delete_user(self, uid: int):
        for g in self.permissions["groups"].values():
            if uid in g:
                g.remove(uid)
        self.known_users.remove(uid)
        self.data.set_json(file="permissions", data=self.permissions)

    def delete_all_users(self):
        for g in self.groups.keys():
            self.groups[g] = []
        self.known_users = []
        self.data.set_json(file="permissions", data=self.permissions)


def is_it_me(ctx, a_id: int) -> bool:
    return ctx.author.id == a_id


def is_owner(ctx) -> bool:
    return ctx.message.author.id == ctx.bot.permit.bot_owner


def is_group_member(*groups: str):
    def in_group(ctx):
        if len(groups) == 0:
            return True
        result = []
        for group in groups:
            result.append(ctx.bot.permit.in_group(ctx.author.id, group))
        return all(result)
    return in_group
