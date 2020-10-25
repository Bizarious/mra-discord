from discord.ext import commands


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


def is_it_me(ctx, a_id):
    return ctx.author.id == a_id


def owner_check(ctx):
    return ctx.message.author.id == ctx.bot.permit.bot_owner


def owner():
    def decorator(ctx):
        return ctx.message.author.id == ctx.bot.permit.bot_owner
    return commands.check(decorator)
