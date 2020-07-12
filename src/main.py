import sys
from bot.bot_client import BotClient
from system_commands import restart


class Main:

    def __init__(self):
        self.bot = BotClient()

    def run(self):
        self.bot.run('NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog')

        if self.bot.restart:
            restart(sys.argv)


if __name__ == "__main__":
    main = Main()
    main.run()
