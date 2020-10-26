from discord.ext import commands


class PermissionsDict:

    def __init__(self, data):
        self.permission_needed = ["bot_owner",
                                  "ignored_users",
                                  "ignored_guilds",
                                  "ignored_channels",
                                  "blacklist"]
        self.data = data
        self.permissions = self.data.load("permissions")
        self.first_startup()

    def first_startup(self):
        changed = False
        for s in self.permission_needed:
            if s not in self.permissions.keys():
                changed = True
                self.permissions[s] = []
        if changed:
            self.data.save(self.permissions, "permissions")

    @property
    def bot_owner(self):
        return self.permissions["bot_owner"]

    @property
    def ignored_users(self):
        return self.permissions["ignored_users"]

    @property
    def ignored_guilds(self):
        return self.permissions["ignored_guilds"]

    @property
    def ignored_channels(self):
        return self.permissions["ignored_channels"]

    @property
    def blacklist(self):
        return self.permissions["blacklist"]

    def add_ignore(self, subject, subject_id):
        real_subject = f"ignored_{subject}"
        self.permissions[real_subject].append(subject_id)
        self.data.save(self.permissions, "permissions")

    def remove_ignore(self, subject, subject_id):
        real_subject = f"ignored_{subject}"
        self.permissions[real_subject].remove(subject_id)
        self.data.save(self.permissions, "permissions")

    def check_ignored(self, message):
        a_id = message.author.id
        c = message.channel
        g = message.guild
        if self.bot_owner == a_id:
            return True
        if a_id not in self.ignored_users:
            if g is not None:
                if g.id not in self.ignored_guilds and \
                        c.id not in self.ignored_channels:
                    return True
        return False


def is_it_me(ctx, a_id):
    return ctx.author.id == a_id


def owner_check(ctx):
    return ctx.message.author.id == ctx.bot.permit.bot_owner


def owner():
    def decorator(ctx):
        return ctx.message.author.id == ctx.bot.permit.bot_owner

    return commands.check(decorator)
