from typing import Optional, TypeVar, ParamSpec
from collections.abc import Callable, Awaitable

import genshin
from genshin.errors import InvalidCookies, GenshinException

from bot.utils.postgres import PostgresConnection


_T = TypeVar('_T')
_P = ParamSpec('_P')


class GenshinClient:
    __slots__ = ('exc_catch', 'cookies', 'client')

    def __init__(self, exc_catch: bool = False, **cookies) -> None:
        self.exc_catch = exc_catch
        self.cookies = cookies

    async def __aenter__(self) -> genshin.Client:
        self.client = genshin.Client(cookies=self.cookies)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        del self.cookies
        del self.client
        if not self.exc_catch:
            return False
        return True


async def is_genshin_account(uid: int, ltoken: str, ltuid: str, cookie_token: str) -> bool:
    async with GenshinClient(ltuid=ltuid, ltoken=ltoken, account_id=ltuid, cookie_token=cookie_token) as client:
        try:
            await client.get_genshin_notes(uid)
            await client.redeem_code('GENSHINGIFT', uid)
            return True
        except InvalidCookies:
            return False
        except GenshinException:
            return True


async def get_genshin_account_by_id(user_id: int) -> Optional[dict[str, int | str]]:
    async with PostgresConnection() as connection:
        account = await connection.fetchrow(f"""
            SELECT * FROM genshin_accounts WHERE user_id = {user_id};
        """)
        return dict(account) if account else None


def catch_hoyolab_errors(func: Callable[_P, Awaitable[_T]]) -> Callable[_P, Awaitable[_T]]:
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        try:
            return await func(*args, **kwargs)
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as exc:
            return f"Необработанная ошибка: {exc}!"
    return wrapper
