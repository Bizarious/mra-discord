import sys
from core.bot import BotClient
from core.system.system_commands import restart
from core.database import Data, ConfigManager
from core.system import IPC
from core.task import TaskManager


class Main:

    def __init__(self):
        self.global_config = ConfigManager()
        self.data = Data()
        self.bot_token = ""
        self.greetings()

        self.ipc = IPC()
        self.ipc.create_queues("bot", "task")

        self.bot = BotClient(self.data, self.global_config, self.ipc)
        self.task_manager = TaskManager(self.data, self.ipc)

    def run(self):
        self.task_manager.start()
        self.bot.run(self.bot_token, reconnect=True)
        t = self.ipc.pack()
        self.ipc.send(dst="task", package=t, cmd="stop")
        self.task_manager.join()

        if self.bot.restart:
            restart(sys.argv, float(self.global_config.get_config("restartTimer")))
        else:
            print("shutdown")

    def greetings(self):
        self.bot_token = self.global_config.get_token("bot")
        if self.bot_token is None:
            self.bot_token = input("\nBot Token: ")
            self.global_config.set_token("bot", self.bot_token)

        bot_owner = self.global_config.get_config("botOwner")
        if bot_owner is None:
            bot_owner = input("\nBot Owner ID: ")
            self.global_config.set_default_config("botOwner", bot_owner)

        self.global_config.set_default_config("restartTimer", "2")


if __name__ == "__main__":
    main = Main()
    main.run()
