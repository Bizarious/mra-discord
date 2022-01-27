from typing import Callable


class IPCMessageHandler:
    """
    Class to handle ipc commands.
    """
    def __init__(self, func: Callable, *ipc_commands: str):
        self._func = func
        self._ipc_commands = ipc_commands

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    @property
    def ipc_commands(self):
        return self._ipc_commands


def on_ipc_message(*ipc_commands: str):
    def decorator(func: Callable):
        return IPCMessageHandler(func, *ipc_commands)
    return decorator
