import asyncio
from typing import TypeVar, Callable, Awaitable
from functools import wraps


_T = TypeVar('_T')


def cycle(
        *,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0
) -> Callable[[Callable[..., Awaitable[_T]]], Callable[..., Awaitable[None]]]:
    """Call inner function in infinite loop with specified period."""
    def decorator(func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[None]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            while True:
                await func(*args, **kwargs)
                await asyncio.sleep(hours * 3600 + minutes * 60 + seconds)
        return wrapper
    return decorator
