from typing import Optional, Literal, List, Dict, Union

from genshin.errors import GenshinException, InvalidCookies

from . import BaseValidator, ChatValidatorMixin
from ..errors.hoyolab import *
from ..utils import GenshinClient
from ..utils.postgres import has_postgres_data
from ..models.hoyolab import GenshinAccount


__all__ = (
    'AccountLinkValidator',
    'AccountUnlinkValidator',
    'HoYoLABValidator',
    'CodeValidator',
    'ResinNotifyValidator',
    'SpiralAbyssValidator'
)


HoYoData = Literal['Notes', 'Stats', 'Rewards', 'Redeem', 'Diary', 'SpiralAbyss']


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
            cookies = {c.lower().split('=')[0] for c in cookies}
            assert {'ltuid', 'ltoken', 'uid', 'cookie_token'} == cookies
        except (IndexError, AssertionError):
            raise CookieSyntaxError

    @staticmethod
    async def check_cookies_valid(account: GenshinAccount) -> None:
        async with GenshinClient(account) as client:
            try:
                await client.get_genshin_notes()
                await client.redeem_code('GENSHINGIFT')
            except InvalidCookies:
                raise InvalidAccountCookies
            except ValueError:
                raise InvalidAccountCookies
            except GenshinException:
                pass


class AccountUnlinkValidator(BaseValidator):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise AccountUnlinked


class HoYoLABValidator(BaseValidator):
    @staticmethod
    def check_account_exist(account: Optional[Dict[str, Union[str, int]]], for_other_user: bool) -> None:
        if not account:
            raise AccountNotExist(for_other_user)

    @staticmethod
    async def check_display_short(cls_name: str, user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM users WHERE {cls_name} = 'long' AND user_id = {user_id};"):
            raise DisplayAlreadyLong

    @staticmethod
    async def check_display_long(cls_name: str, user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM users WHERE {cls_name} = 'short' AND user_id = {user_id};"):
            raise DisplayAlreadyShort

    @staticmethod
    def check_display_type_correct(d_type: str) -> None:
        correct_types = ('short', 'long')
        if d_type not in correct_types:
            raise IncorrectDisplayType(d_type)


class CodeValidator(HoYoLABValidator):
    @staticmethod
    def check_display_short(cls_name: str, user_id: int) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_display_long(cls_name: str, user_id: int) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_display_type_correct(d_type: str) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_code_specified(codes: List[str]) -> None:
        if not codes:
            raise RedeemCodeNotSpecified


class ResinNotifyValidator(BaseValidator, ChatValidatorMixin):
    @staticmethod
    async def check_account_linked(user_id: int) -> None:
        if not await has_postgres_data(f"SELECT * FROM genshin_accounts WHERE user_id = {user_id};"):
            raise CommandNotAllowed

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

    @staticmethod
    async def check_notifications_disabled(user_id: int, chat_id: int) -> None:
        if not await has_postgres_data(f"""
                SELECT * from users_in_chats 
                WHERE user_id = {user_id} AND chat_id = {chat_id} AND resin_notifications = false;
        """):
            raise NotificationsAlreadyEnabled


class SpiralAbyssValidator(HoYoLABValidator):
    @staticmethod
    def check_display_short(cls_name: str, user_id: int) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_display_long(cls_name: str, user_id: int) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_display_type_correct(d_type: str) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_abyss_unlocked(status: bool) -> None:
        if not status:
            raise SpiralAbyssLocked
