from typing import Optional
from re import Match

from vkbottle import API
from vkbottle_types.objects import MessagesForeignMessage, MessagesMessageAttachment

from . import BaseValidator
from ..errors.default import *
from ..utils.postgres import has_postgres_data
from ..config.dependencies import group


__all__ = (
    'ChoiceValidator',
    'AutocorrectionValidator',
    'ConvertValidator',
    'TimerValidator',
    'AttachmentForwardValidator',
    'RandomPictureValidator'
)


class ChoiceValidator(BaseValidator):
    @staticmethod
    def check_choice_options_specified(choice_options: list[str]) -> None:
        if not choice_options:
            raise ChoiceOptionsNotSpecified


class AutocorrectionValidator(BaseValidator):
    @staticmethod
    async def check_autocorrection_disabled(user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM users WHERE user_id = {user_id} AND autocorrect = true;"):
            raise AutocorrectionAlreadyEnabled

    @staticmethod
    async def check_autocorrection_enabled(user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM users WHERE user_id = {user_id} AND autocorrect = false;"):
            raise AutocorrectionAlreadyDisabled


class ConvertValidator(BaseValidator):
    @staticmethod
    def check_reply_message(reply_message: Optional[MessagesForeignMessage]) -> None:
        if not reply_message:
            raise ReplyMessageError

    @staticmethod
    def check_reply_message_text(text: str) -> None:
        if not text:
            raise ReplyMessageTextError


class TimerValidator(BaseValidator):
    @staticmethod
    def check_timer_specified(text: str) -> None:
        if not text:
            raise TimerNotSpecified

    @staticmethod
    def check_timer_syntax(countdown: Optional[int]) -> None:
        if not countdown:
            raise TimerSyntaxError


class AttachmentForwardValidator(BaseValidator):
    @staticmethod
    def check_attachments(attachments: Optional[list[MessagesMessageAttachment]]) -> None:
        if not attachments:
            raise AttachmentError

    @staticmethod
    def check_attachment_response(response: list[str]) -> None:
        if not response:
            raise AttachmentTypeError


class RandomPictureValidator(BaseValidator):
    @staticmethod
    async def check_user_is_don(api: API, user_id: int):
        donuts = await api.groups.get_members(group.SHORTNAME[1:], filter='donut')
        if user_id not in donuts.items:
            raise UserIsNotDon

    @staticmethod
    def check_fav_count_defined(fav_count: Optional[Match]) -> None:
        if fav_count is None:
            raise FavCountNotDefined

    @staticmethod
    def check_fav_count_range(fav_count: int):
        if not 0 <= fav_count <= 5000:
            raise FavCountRangeInvalid

    @staticmethod
    def check_picture_quantity_specified(query: list[str]) -> None:
        if not query or not query[0].isdigit():
            raise PictureQuantityNotSpecified

    @staticmethod
    def check_picture_quantity(quantity: int) -> None:
        if quantity > 10:
            raise PictureQuantityOverflow

    @staticmethod
    def check_tag_quantity(tags: tuple[str, ...], is_interactive: bool) -> None:
        if len(tags) > (2 if is_interactive else 3):
            raise TagQuantityOverflow(is_interactive)
