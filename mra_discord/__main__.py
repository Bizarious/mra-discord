from mra_discord.core import Bot
from .__token__ import __token__

b = Bot(paths=["mra_discord/core/extensions"])
b.run(__token__)
