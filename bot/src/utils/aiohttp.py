from typing import Callable, Awaitable, Optional, TypeVar
from functools import wraps
from asyncio.exceptions import TimeoutError

from aiohttp.client_exceptions import ClientError


_T = TypeVar('_T')


def catch_aiohttp_errors(func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[Optional[_T]]]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Optional[_T]:
        try:
            return await func(*args, **kwargs)
        except (TimeoutError, ClientError):
            return None
    return wrapper
