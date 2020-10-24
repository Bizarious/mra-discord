import sys
from bot.bot_client import BotClient
from system.system_commands import restart
from bot.database import Data
from system.ipc import IPC
from task.task_control import TaskManager


class Main:

    def __init__(self):
        self.data = Data()
        self.bot_token = ""
        self.greetings()

        self.ipc = IPC()
        self.ipc.create_queues("bot", "task")

        self.bot = BotClient(self.data, self.ipc)
        self.task_manager = TaskManager(self.ipc, {})

    def run(self):
        self.task_manager.start()
        self.bot.run(self.bot_token)

        t = self.ipc.pack()
        self.ipc.send(dst="task", package=t, cmd="stop")

        if self.bot.restart:
            restart(sys.argv)

    def greetings(self):
        tokens: dict = self.data.load("tokens")
        if "bot" not in tokens.keys():
            bot_token = input("Bot Token: ")
            tokens["bot"] = bot_token
            self.data.save(tokens, "tokens")
        self.bot_token = tokens["bot"]

        permissions: dict = self.data.load("permissions")
        if "bot_owner" not in permissions.keys():
            bot_owner = int(input("Bot Owner ID: "))
            permissions["bot_owner"] = bot_owner
            self.data.save(permissions, "permissions")


if __name__ == "__main__":
    main = Main()
    main.run()
