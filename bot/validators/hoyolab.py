from typing import Optional, Literal, TypeAlias

from vkbottle.bot import Message
from vkbottle_types.objects import MessagesForeignMessage

from bot.validators import BaseValidator, ChatValidator
from bot.errors.hoyolab import *
from bot.utils.postgres import has_postgres_data
from bot.utils.genshin import is_genshin_account


__all__ = (
    'AccountLinkValidator',
    'AccountUnlinkValidator',
    'HoYoLABValidator',
    'CodeValidator',
    'ResinNotifyValidator',
    'SpiralAbyssValidator'
)


HoYoData: TypeAlias = Literal['Notes', 'Stats', 'Rewards', 'Redeem', 'Diary', 'SpiralAbyss']


class AccountLinkValidator(BaseValidator):
    @staticmethod
    async def check_account_new(user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise AccountAlreadyLinked

    @staticmethod
    def check_cookie_amount(cookies: list[str]) -> None:
        if not cookies or len(cookies) != 4:
            raise NotEnoughCookies

    @staticmethod
    def check_cookie_syntax(cookies: list[str]) -> None:
        try:
            cookies = {c.lower().split('=')[0] for c in cookies}
            assert {'ltuid', 'ltoken', 'uid', 'cookie_token'} == cookies
        except (IndexError, AssertionError):
            raise CookieSyntaxError

    @staticmethod
    async def check_cookies_valid(cookies: dict[str, str]) -> None:
        if not await is_genshin_account(**cookies):
            raise InvalidAccountCookies


class AccountUnlinkValidator(BaseValidator):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise AccountUnlinked


class HoYoLABValidator(BaseValidator):
    def __init__(
            self,
            message: Message,
            datatype: HoYoData
    ) -> None:
        super().__init__(message)
        self._datatype = datatype

    def check_reply_message(self, reply_message: Optional[MessagesForeignMessage]) -> None:
        if not reply_message:
            raise ReplyMessageError(self._datatype)

    @staticmethod
    def check_account_exist(account: Optional[dict[str, str | int]], for_other_user: bool = False) -> None:
        if not account:
            raise AccountNotExist(for_other_user)


class CodeValidator(HoYoLABValidator):
    @staticmethod
    def check_code_specified(codes: list[str]) -> None:
        if not codes:
            raise RedeemCodeNotSpecified


class ResinNotifyValidator(BaseValidator, ChatValidator):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise CommandNotAllowed

    @staticmethod
    async def check_notifications_disabled(user_id: int, chat_id: int) -> None:
        if not await has_postgres_data(f"""
                SELECT * from users_in_chats 
                WHERE user_id = {user_id} AND chat_id = {chat_id} AND resin_notifications = false;
        """):
            raise NotificationsAlreadyEnabled

    @staticmethod
    def check_value_valid(value: str) -> None:
        try:
            int(value)
        except ValueError:
            raise NotificationValueInvalid

    @staticmethod
    def check_value_range(value: int):
        if not 0 <= value <= 160:
            raise NotificationValueRangeInvalid

    @staticmethod
    async def check_notifications_enabled(user_id: int, chat_id: int) -> None:
        if not await has_postgres_data(f"""
                SELECT * from users_in_chats 
                WHERE user_id = {user_id} AND chat_id = {chat_id} AND resin_notifications = true;
        """):
            raise NotificationsAlreadyDisabled


class SpiralAbyssValidator(HoYoLABValidator):
    @staticmethod
    def check_abyss_unlocked(status: bool) -> None:
        if not status:
            raise SpiralAbyssLocked
