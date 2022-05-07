from bot.src.constants import COMMANDS
from bot.utils.postgres import has_postgres_data
from bot.errors.customcommands import *


__all__ = (
    'CreationValidator',
)


class BaseValidator:
    def __init__(self, api) -> None:
        self._api = api

    async def _check_for_privileges(self, chat_id: int, user_id: int) -> bool:
        chat = await self._api.messages.get_conversation_members(peer_id=chat_id)
        for user in chat.items:
            if user.member_id == user_id and any((user.is_owner, user.is_admin)):
                return True
        return False


class CreationValidator(BaseValidator):
    def __init__(self, api) -> None:
        super().__init__(api)

    async def check_availability(self, chat_id: int, from_id: int) -> None:
        conditions = [
            await has_postgres_data(f"SELECT * FROM chats WHERE chat_id = {chat_id} and ffa_commands = true;"),
            await self._check_for_privileges(chat_id, from_id)
        ]
        if not any(conditions):
            raise AvailabilityError

    @staticmethod
    def check_name(name: str) -> None:
        if not name:
            raise EmptyNameError

    @staticmethod
    async def check_already_exists(name: str, chat_id: int) -> None:
        if await has_postgres_data(f"SELECT * FROM custom_commands WHERE name = '{name}' AND chat_id = {chat_id};"):
            raise CommandExistsError(name)

    @staticmethod
    def check_reserved(name: str) -> None:
        if name in COMMANDS:
            raise CommandReservedError(name)

    @staticmethod
    def check_additions(additions: list) -> None:
        if not any(additions):
            raise NotAnyAdditionError
