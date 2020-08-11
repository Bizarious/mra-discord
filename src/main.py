import sys
from bot.bot_client import BotClient
from system_commands import restart
from bot.database import Data
from task.task_control import TaskManager


class Main:

    def __init__(self):
        self.data = Data()
        self.bot = BotClient(self.data)
        self.task_manager = TaskManager(self.bot.queue_task, self.bot.queue_in, "a")

    def run(self):
        self.task_manager.start()
        self.bot.run('NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog')
        self.bot.queue_task.put("Stop")

        if self.bot.restart:
            restart(sys.argv)


if __name__ == "__main__":
    main = Main()
    main.run()
