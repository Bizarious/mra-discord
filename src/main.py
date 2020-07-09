import os
import sys
from bot.bot_client import BotClient

bot = BotClient()

bot.run('NjQxMzg0OTg5MTk1NTAxNTY4.XcHmhQ.9oqoxjRIn8EZMgZuerimKM_pjog')
if bot.restart:
    os.execv(sys.executable, [sys.executable.split("/")[-1]] + sys.argv)
