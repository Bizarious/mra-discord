from discord.ext import commands
from bot.database import Data
import json


class PermissionsDict:

    def __init__(self, data):
        self.data = data
        self.permissions = self.data.load("permissions")

    @property
    def bot_owner(self):
        return self.permissions["bot_owner"]

    @property
    def users(self):
        return self.permissions["users"]

    @property
    def guilds(self):
        return self.permissions["guilds"]

    @property
    def channels(self):
        return self.permissions["channels"]

    @property
    def blacklist(self):
        return self.permissions["blacklist"]

    def add_ignore(self, subject, subject_id):
        if subject not in self.permissions.keys():
            self.permissions[subject] = []
        self.permissions[subject].append(subject_id)
        self.data.save(self.permissions, "permissions")

    def remove_ignore(self, subject, subject_id):
        self.permissions[subject].remove(subject_id)
        self.data.save(self.permissions, "permissions")


def is_it_me():
    def decorator(ctx):
        f = open(f"{Data.path_data}/permissions.json")
        return ctx.message.author.id == json.load(f)["bot_owner"]
    return commands.check(decorator)
