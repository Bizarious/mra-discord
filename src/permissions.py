from discord.ext import commands


class PermissionsDict:

    def __init__(self, data):
        self.data = data
        self.permissions = self.data.load_permissions()

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
        self.permissions[subject].append(subject_id)
        self.data.save_permissions(self.permissions)

    def remove_ignore(self, subject, subject_id):
        self.permissions[subject].remove(subject_id)
        self.data.save_permissions(self.permissions)


def is_it_me():
    def decorator(ctx):
        return ctx.message.author.id == 525020069772656660
    return commands.check(decorator)
