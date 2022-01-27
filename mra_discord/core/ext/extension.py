from typing import Optional, Any, Callable
from .errors import OnMessageLimiterError


class Extension:

    def __init__(self, *,
                 cls: Any,
                 name: str,
                 target: Optional[str],
                 auto_load: Optional[bool] = False,
                 can_unload: Optional[bool] = True
                 ):

        self._cls = cls

        if name is None:
            self._name = cls.__name__
        else:
            self._name = name

        self._auto_load = auto_load
        self._can_unload = can_unload
        self._target = target

        # represents the loaded extension
        self._extension = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def cls(self) -> Any:
        return self._cls

    @property
    def auto_load(self) -> bool:
        return self._auto_load

    @property
    def can_unload(self) -> bool:
        return self._can_unload

    @property
    def target(self) -> str:
        return self._target

    @property
    def loaded(self) -> bool:
        return self._extension is not None

    @property
    def extension(self):
        return self._extension

    def load(self, interface, *args, **kwargs):
        self._extension = self._cls(interface, *args, **kwargs)
        if hasattr(self._extension, "on_load"):
            self._extension.on_load()

    def unload(self):
        if hasattr(self._extension, "on_unload"):
            self._extension.on_unload()
        self._extension = None


def extension(*,
              name: Optional[str] = None,
              auto_load: Optional[bool] = False,
              can_unload: Optional[bool] = True,
              target: Optional[str] = None
              ):

    def dec(cls):
        old_init = cls.__init__

        def new__init__(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            self._given_name = name or self.__class__.__name__

        @property
        def given_name(self):
            return self._given_name

        cls.__init__ = new__init__
        cls.given_name = given_name

        return Extension(cls=cls,
                         name=name,
                         auto_load=auto_load,
                         can_unload=can_unload,
                         target=target
                         )
    return dec


class OnMessageLimiter:
    """
    Class to restrict command execution in the on_message method.
    """
    def __init__(self, func: Callable):
        self._func = func

    async def __call__(self, *args, **kwargs) -> bool:
        result = await self._func(*args, **kwargs)
        if not isinstance(result, bool):
            raise OnMessageLimiterError(f"The function must return bool")
        return result


def limit_on_message(func: Callable):
    return OnMessageLimiter(func)


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
