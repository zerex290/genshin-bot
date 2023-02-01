import asyncio
from collections.abc import Callable, Awaitable
from typing import TypeVar, ParamSpec
from functools import wraps


_T = TypeVar('_T')
_P = ParamSpec('_P')


def cycle(
        *,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0
) -> Callable[[Callable[_P, Awaitable[_T]]], Callable[_P, Awaitable[None]]]:
    """Call inner function in infinite loop with specified period."""
    def decorator(func: Callable[_P, Awaitable[_T]]) -> Callable[_P, Awaitable[None]]:
        @wraps(func)
        async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> None:
            while True:
                await func(*args, **kwargs)
                await asyncio.sleep(hours * 3600 + minutes * 60 + seconds)
        return wrapper
    return decorator
