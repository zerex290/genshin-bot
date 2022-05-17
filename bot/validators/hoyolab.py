from typing import List, Dict, Optional

from vkbottle.bot import Message
from vkbottle_types.objects import MessagesForeignMessage

from bot.validators import BaseValidator
from bot.errors.hoyolab import *
from bot.utils.postgres import has_postgres_data
from bot.utils.genshin import is_genshin_account


__all__ = (
    'AccountLinkValidator',
    'AccountUnlinkValidator',
    'GenshinDataValidator',
    'RedeemCodeValidator',
    'ResinNotifyValidator'
)


class AccountLinkValidator(BaseValidator):
    @staticmethod
    async def check_account_new(user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise AccountAlreadyLinked

    @staticmethod
    def check_cookie_amount(cookies: List[str]) -> None:
        if not cookies or len(cookies) != 4:
            raise NotEnoughCookies

    @staticmethod
    def check_cookie_syntax(cookies: List[str]) -> None:
        try:
            cookies = {c.lower().split('=')[0]: c.split('=')[1] for c in cookies}
            assert {'ltuid', 'ltoken', 'uid', 'cookie_token'} == set(cookies)
        except (IndexError, AssertionError):
            raise CookieSyntaxError

    @staticmethod
    async def check_cookies_valid(cookies: Dict[str, str]) -> None:
        if not await is_genshin_account(**cookies):
            raise InvalidAccountCookies


class AccountUnlinkValidator(BaseValidator):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise AccountNotExists


class GenshinDataValidator(BaseValidator):
    def __init__(self, message: Message, datatype: str) -> None:
        """
        :param datatype: Can be 'Notes', 'Stats', 'Rewards' or 'Diary'
        """
        super().__init__(message)
        self._datatype = datatype

    def check_reply_message(self, reply_message: Optional[MessagesForeignMessage]) -> None:
        if not reply_message:
            raise ReplyMessageError(self._datatype)

    @staticmethod
    def check_account_exists(account: Optional[Dict[str, str | int]], for_other_user: bool = False) -> None:
        if not account:
            raise AccountNotFound(for_other_user)


class RedeemCodeValidator(GenshinDataValidator):
    @staticmethod
    def check_redeem_specified(codes: List[str]) -> None:
        if not codes:
            raise RedeemCodeNotSpecified


class ResinNotifyValidator(BaseValidator):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise CommandNotAllowed
