import os
import logging

from dotenv import load_dotenv
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue

from core import Bot, BOT_IDENTIFIER
from core.task import TASK_HANDLER_IDENTIFIER

import nextcord


if __name__ == "__main__":
    # logger setup bot
    _LOGGER_FORMAT = "[{asctime}]  {name: <4}  {levelname: <8}  {message}"
    _LOG_LEVEL = logging.INFO

    _log_formatter = logging.Formatter(_LOGGER_FORMAT, style="{")

    _log_handler = logging.StreamHandler()
    _log_handler.setLevel(_LOG_LEVEL)
    _log_handler.setFormatter(_log_formatter)

    _logger = logging.getLogger(BOT_IDENTIFIER)
    _logger.setLevel(_LOG_LEVEL)
    _logger.addHandler(_log_handler)

    # logger setup task
    _logging_queue = Queue()
    _queue_handler = QueueHandler(_logging_queue)
    _queue_handler.setLevel(_LOG_LEVEL)
    _queue_handler.setFormatter(_log_formatter)

    _task_logger = logging.getLogger(TASK_HANDLER_IDENTIFIER)
    _task_logger.setLevel(_LOG_LEVEL)
    _task_logger.addHandler(_queue_handler)

    _log_handler_queue = logging.StreamHandler()
    _log_handler_queue.setLevel(_LOG_LEVEL)

    _listener = QueueListener(_logging_queue, _log_handler_queue)
    _listener.start()

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

    _listener.stop()
