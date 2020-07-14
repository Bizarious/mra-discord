import sys
from bot.bot_client import BotClient
from system_commands import restart
from multiprocessing import Queue
from bot.database import Data


class Main:

    def __init__(self):
        self.data = Data()
        self.bot = BotClient(self.data)

    def run(self):
        self.bot.run('NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog')

        if self.bot.restart:
            restart(sys.argv)


if __name__ == "__main__":
    main = Main()
    main.run()
