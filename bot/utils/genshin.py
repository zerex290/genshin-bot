from typing import Optional

import genshin
from genshin.errors import InvalidCookies, GenshinException

from bot.utils.postgres import PostgresConnection


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


async def get_genshin_account_by_id(
        user_id: int,
        uid: bool = False,
        ltuid: bool = False,
        ltoken: bool = False,
        cookie_token: bool = False
) -> Optional[dict[str, int | str]]:
    async with PostgresConnection() as connection:
        columns = []
        parameters = {'uid': uid, 'ltuid': ltuid, 'ltoken': ltoken, 'cookie_token': cookie_token}
        for parameter in parameters:
            if parameters[parameter]:
                columns.append(parameter)
        account = await connection.fetchrow(f"""
            SELECT {', '.join(columns)} FROM genshin_accounts WHERE user_id = {user_id};
        """)
        return dict(account) if account else None
