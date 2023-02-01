from typing import Optional

from vkbottle_types.objects import MessagesForeignMessage, MessagesKeyboard

from . import BaseValidator
from ..errors.genshindb import *
from ..utils.postgres import has_postgres_data


__all__ = ('GenshinDBValidator',)


class GenshinDBValidator(BaseValidator):
    @staticmethod
    def check_shortcut_specified(name: str) -> None:
        if not name:
            raise ShortcutNotSpecified

    @staticmethod
    async def check_shortcut_new(name: str, user_id: int) -> None:
        if await has_postgres_data(
                f"SELECT * FROM genshindb_shortcuts WHERE user_id = {user_id} AND shortcut = '{name}';"
        ):
            raise ShortcutAlreadyExist(name)

    @staticmethod
    async def check_shortcut_exist(name: str, user_id: int) -> None:
        if not await has_postgres_data(
            f"SELECT * FROM genshindb_shortcuts WHERE user_id = {user_id} AND shortcut = '{name}';"
        ):
            raise ShortcutNotExist(name)

    @staticmethod
    def check_reply_message(reply_message: Optional[MessagesForeignMessage]) -> None:
        if not reply_message:
            raise ReplyMessageError

    @staticmethod
    def check_reply_message_keyboard(keyboard: Optional[MessagesKeyboard]) -> None:
        if not keyboard:
            raise WrongReplyMessage

    @staticmethod
    def check_keyboard_handler(keyboard: MessagesKeyboard, handler: str) -> None:
        if eval(keyboard.buttons[0][0]['action']['payload']).get('handler') != handler:
            raise WrongReplyMessage

    @staticmethod
    async def check_shortcuts_created(user_id: int) -> None:
        if not await has_postgres_data(
            f"SELECT * FROM genshindb_shortcuts WHERE user_id = {user_id};"
        ):
            raise ShortcutsNotCreated
