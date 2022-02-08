import os
import logging

from dotenv import load_dotenv

from core import Bot, BOT_IDENTIFIER

import nextcord


if __name__ == "__main__":
    # logger setup
    _LOGGER_FORMAT = "[{asctime}]  {name: <4}  {levelname: <8}  {message}"
    _LOG_LEVEL = logging.INFO

    _log_formatter = logging.Formatter(_LOGGER_FORMAT, style="{")

    _log_handler = logging.StreamHandler()
    _log_handler.setLevel(_LOG_LEVEL)
    _log_handler.setFormatter(_log_formatter)

    _logger = logging.getLogger(BOT_IDENTIFIER)
    _logger.setLevel(_LOG_LEVEL)
    _logger.addHandler(_log_handler)

    load_dotenv()

    token = os.environ.get("TOKEN_DISCORD")
    if token is None:
        raise ValueError("Please provide a discord token.")

    intents = nextcord.Intents.all()

    b = Bot(extension_paths=["core/extensions"],
            data_path="data",
            intents=intents
            )
    b.run(token)
