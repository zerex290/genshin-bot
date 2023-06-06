from typing import Optional, TypeVar, ParamSpec
from collections.abc import Callable, Awaitable
from functools import wraps

import genshin
from genshin.errors import InvalidCookies, GenshinException

from ..utils.postgres import PostgresConnection
from ..models.hoyolab import GenshinAccount


_T = TypeVar('_T')
_P = ParamSpec('_P')


class GenshinClient:
    def __init__(self, account: GenshinAccount, *, exc_catch: bool = False) -> None:
        self.account = account
        self.exc_catch = exc_catch

    async def __aenter__(self) -> genshin.Client:
        client = genshin.Client(game=genshin.Game.GENSHIN, uid=self.account.uid)
        client.set_cookies(
            ltuid=self.account.ltuid,
            ltoken=self.account.ltoken,
            account_id=self.account.account_id,
            cookie_token=self.account.cookie_token
        )
        return client

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        return self.exc_catch


async def get_genshin_account_by_id(user_id: int) -> Optional[GenshinAccount]:
    async with PostgresConnection() as connection:
        account = await connection.fetchrow(f"""
            SELECT * FROM genshin_accounts WHERE user_id = {user_id};
        """)
        return GenshinAccount(**dict(account)) if account else None


def catch_hoyolab_errors(func: Callable[_P, Awaitable[_T]]) -> Callable[_P, Awaitable[_T]]:
    @wraps(func)
    async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T | str:
        try:
            return await func(*args, **kwargs)  # noqa
        except InvalidCookies:
            return 'Ошибка: указанные игровые данные больше недействительны!'
        except GenshinException as exc:
            return f"Необработанная ошибка: {exc}"
    return wrapper
