from typing import List, Tuple, Optional

from vkbottle_types.objects import MessagesForeignMessage, MessagesMessageAttachment

from bot.validators import BaseValidator
from bot.errors.default import *
from bot.utils.postgres import has_postgres_data


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
    def check_choice_options_specified(choice_options: List[str]) -> None:
        if not choice_options:
            raise ChoiceOptionsNotSpecified


class AutocorrectionValidator(BaseValidator):
    @staticmethod
    async def check_autocorrection_already_enabled(user_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM users WHERE user_id = {user_id} AND autocorrect = true;"):
            raise AutocorrectionAlreadyEnabled

    @staticmethod
    async def check_autocorrection_already_disabled(user_id: int) -> None:
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
    def check_attachments(attachments: Optional[List[MessagesMessageAttachment]]) -> None:
        if not attachments:
            raise AttachmentError

    @staticmethod
    def check_attachment_response(response: List[str]) -> None:
        if not response:
            raise AttachmentTypeError


class RandomPictureValidator(BaseValidator):
    @staticmethod
    def check_pictures_specified(query: List[str]) -> None:
        if not query or not query[0].isdigit():
            raise PictureQuantityNotSpecified

    @staticmethod
    def check_pictures_quantity(quantity: int) -> None:
        if quantity > 10:
            raise PictureQuantityOverflow

    @staticmethod
    def check_tags_quantity(tags: Tuple[str, ...]) -> None:
        if len(tags) > 3:
            raise TagQuantityOverflow
