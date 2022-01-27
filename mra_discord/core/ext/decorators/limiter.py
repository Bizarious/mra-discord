from typing import Callable
from core.ext import OnMessageLimiterError


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
