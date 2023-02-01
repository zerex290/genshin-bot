from typing import Optional

from vkbottle import API, VKAPIError

from . import BaseValidator, ChatValidatorMixin
from ..utils.postgres import has_postgres_data
from ..errors.customcommands import *


__all__ = (
    'CreationValidator',
    'DeletionValidator',
    'ViewValidator',
    'CommandValidator'
)


class CommandValidatorMixin:
    @staticmethod
    def check_additions_specified(additions: list) -> None:
        if not any(additions):
            raise AdditionsNotSpecified

    @staticmethod
    def check_addition_quantity(doc_id: str, audio_id: str, photo_id: str) -> None:
        additions = []
        for addition in list(locals().copy().values())[:-1]:
            if addition:
                additions.extend(addition.split(','))
        if len(additions) > 4:
            raise AdditionQuantityOverflow

    @staticmethod
    async def is_privileged(api: API, chat_id: int, user_id: int) -> Optional[bool]:
        try:
            chat = await api.messages.get_conversation_members(peer_id=chat_id)
            for user in chat.items:
                if user.member_id == user_id and any((user.is_owner, user.is_admin)):
                    return True
            return False
        except VKAPIError[917]:
            raise BotPrivilegesError

    @classmethod
    async def check_availability(cls, api: API, chat_id: int, user_id: int) -> None:
        conditions = [
            await has_postgres_data(f"SELECT * FROM chats WHERE chat_id = {chat_id} and ffa_commands = true;"),
            await cls.is_privileged(api, chat_id, user_id)
        ]
        if not any(conditions):
            raise AvailabilityError

    @staticmethod
    def check_command_specified(name: str) -> None:
        if not name:
            raise CommandNotSpecified


class CommandValidator(BaseValidator, CommandValidatorMixin):
    @staticmethod
    def check_command_specified(name: str) -> None:
        raise AttributeError('This method is unavailable!')


class CreationValidator(BaseValidator, ChatValidatorMixin, CommandValidatorMixin):
    @staticmethod
    async def check_command_new(name: str, chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM custom_commands WHERE name = $1 AND chat_id = {chat_id};", name):
            raise CommandAlreadyExist(name)


class DeletionValidator(BaseValidator, ChatValidatorMixin, CommandValidatorMixin):
    @staticmethod
    async def check_command_exist(name: str, chat_id: int):
        if not await has_postgres_data(f"SELECT * FROM custom_commands WHERE name = $1 AND chat_id = {chat_id};", name):
            raise CommandNotExist

    @staticmethod
    def check_additions_specified(additions: list) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_addition_quantity(doc_id: str, audio_id: str, photo_id: str) -> None:
        raise AttributeError('This method is unavailable!')


class ViewValidator(BaseValidator, ChatValidatorMixin, CommandValidatorMixin):
    @classmethod
    async def check_privileges(cls, api: API, chat_id: int, user_id: int) -> None:
        if not await cls.is_privileged(api, chat_id, user_id):
            raise PrivilegesError

    @staticmethod
    async def check_actions_restricted(chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM chats WHERE ffa_commands = true AND chat_id = {chat_id};"):
            raise ActionsAlreadyPublic

    @staticmethod
    async def check_actions_public(chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM chats WHERE ffa_commands = false AND chat_id = {chat_id};"):
            raise ActionsAlreadyRestricted

    @staticmethod
    def check_additions_specified(additions: list) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_addition_quantity(doc_id: str, audio_id: str, photo_id: str) -> None:
        raise AttributeError('This method is unavailable!')

    @classmethod
    async def check_availability(cls, api: API, chat_id: int, user_id: int) -> None:
        raise AttributeError('This method is unavailable!')

    @staticmethod
    def check_command_specified(name: str) -> None:
        raise AttributeError('This method is unavailable!')
