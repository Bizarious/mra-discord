from core import Bot
from __token__ import __token__

import nextcord

if __name__ == "__main__":
    intents = nextcord.Intents.default()
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.presences = True
    # noinspection PyDunderSlots,PyUnresolvedReferences
    intents.members = True

    b = Bot(extension_paths=["core/extensions"],
            data_path="data",
            intents=intents
            )
    b.run(__token__)
