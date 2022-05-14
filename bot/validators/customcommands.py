from vkbottle import API

from bot.validators import BaseValidator
from bot.src.constants import COMMANDS
from bot.utils.postgres import has_postgres_data
from bot.errors.customcommands import *
from bot.src.models.customcommands import ChatCustomCommands


__all__ = (
    'CreationValidator',
    'DeletionValidator',
    'ViewValidator'
)


async def _check_privileges(api: API, chat_id: int, user_id: int) -> bool:
    chat = await api.messages.get_conversation_members(peer_id=chat_id)
    for user in chat.items:
        if user.member_id == user_id and any((user.is_owner, user.is_admin)):
            return True
    return False


async def _check_availability(api: API, chat_id: int, user_id: int) -> bool:
    conditions = [
        await has_postgres_data(f"SELECT * FROM chats WHERE chat_id = {chat_id} and ffa_commands = true;"),
        await _check_privileges(api, chat_id, user_id)
    ]
    return True if any(conditions) else False


class CreationValidator(BaseValidator):
    async def check_availability(self, chat_id: int, user_id: int) -> None:
        if not await _check_availability(self._message.ctx_api, chat_id, user_id):
            raise ManipulationError

    @staticmethod
    def check_command_specified(name: str) -> None:
        if not name:
            raise CommandNotSpecified

    @staticmethod
    async def check_command_new(name: str, chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM custom_commands WHERE name = '{name}' AND chat_id = {chat_id};"):
            raise CommandExists(name)

    @staticmethod
    def check_command_not_reserved(name: str) -> None:
        if name in COMMANDS:
            raise CommandReserved(name)

    @staticmethod
    def check_additions_specified(additions: list) -> None:
        if not any(additions):
            raise AdditionNotSpecified


class DeletionValidator(BaseValidator):
    async def check_availability(self, chat_id: int, user_id: int) -> None:
        if not await _check_availability(self._message.ctx_api, chat_id, user_id):
            raise ManipulationError

    @staticmethod
    def check_command_specified(name: str) -> None:
        if not name:
            raise CommandNotSpecified

    @staticmethod
    async def check_command_exists(name: str, chat_id: int):
        if not await has_postgres_data(f"SELECT * FROM custom_commands WHERE name = '{name}' AND chat_id = {chat_id};"):
            raise CommandNotExists


class ViewValidator(BaseValidator):
    @staticmethod
    def check_created(custom_commands: ChatCustomCommands) -> None:
        if not custom_commands:
            raise CommandsNotCreated

    @staticmethod
    async def check_privileges(api: API, chat_id: int, user_id: int) -> None:
        if not await _check_privileges(api, chat_id, user_id):
            raise AvailabilityError

    @staticmethod
    async def check_not_public(chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM chats WHERE ffa_commands = true AND chat_id = {chat_id};"):
            raise AlreadyPublic

    @staticmethod
    async def check_not_restricted(chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM chats WHERE ffa_commands = false AND chat_id = {chat_id};"):
            raise AlreadyRestricted
