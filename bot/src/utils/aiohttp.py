from typing import Callable, Awaitable, Optional, TypeVar, ParamSpec
from functools import wraps
from asyncio.exceptions import TimeoutError

from aiohttp.client_exceptions import ClientError


_T = TypeVar('_T')
_P = ParamSpec('_P')


def catch_aiohttp_errors(func: Callable[_P, Awaitable[_T]]) -> Callable[_P, Awaitable[Optional[_T]]]:
    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> Optional[_T]:
        try:
            return await func(*args, **kwargs)  # noqa
        except (TimeoutError, ClientError):
            return None
    return wrapper
