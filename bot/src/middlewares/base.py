import re
from typing import Optional
from functools import lru_cache

from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle_types.objects import MessagesMessageActionStatus

from ..utils import PostgresConnection
from ..utils.postgres import has_postgres_data
from ..constants import keyboard, COMMANDS


__all__ = (
    'GroupFilterMiddleware',
    'UserRegisterMiddleware',
    'ChatRegisterMiddleware',
    'ChatUserUpdateMiddleware',
    'CommandGuesserMiddleware',
)


ACTIONS = [
    MessagesMessageActionStatus.CHAT_INVITE_USER,
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_MESSAGE_REQUEST,
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK,
    MessagesMessageActionStatus.CHAT_KICK_USER
]


class MiddlewareMixin:
    @staticmethod
    async def insert_into_users(user_id: int) -> None:
        if await has_postgres_data(f"SELECT user_id FROM users WHERE user_id = {user_id};"):
            return None
        async with PostgresConnection() as connection:
            await connection.execute(f"INSERT INTO users VALUES ({user_id});")


class GroupFilterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if self.event.from_id < 0:
            self.stop()


class UserRegisterMiddleware(BaseMiddleware[Message], MiddlewareMixin):
    async def pre(self) -> None:
        if self.event.from_id < 0:  #: Filter groups from inserting into database
            return None
        await self.insert_into_users(self.event.from_id)


class ChatRegisterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        chat_id = self.event.peer_id
        if chat_id < 2e9 or await has_postgres_data(f"SELECT * FROM chats WHERE chat_id = {chat_id}"):
            return None
        async with PostgresConnection() as connection:
            await connection.execute(f"INSERT INTO chats VALUES ({chat_id});")


class ChatUserUpdateMiddleware(BaseMiddleware[Message], MiddlewareMixin):
    async def pre(self) -> None:
        chat_id = self.event.peer_id
        user_id = self.event.from_id
        if chat_id > 2e9 and not await has_postgres_data(
                f"SELECT * FROM users_in_chats WHERE chat_id = {chat_id} AND user_id = {user_id};"
        ):
            async with PostgresConnection() as connection:
                await connection.execute(f"INSERT INTO users_in_chats VALUES ({user_id}, {chat_id});")
        if not self.event.action or self.event.action.type not in ACTIONS:
            return None
        user_id = self.event.action.member_id
        action_type = self.event.action.type
        if action_type == MessagesMessageActionStatus.CHAT_KICK_USER:
            async with PostgresConnection() as connection:
                await connection.execute(
                    f"DELETE FROM users_in_chats WHERE chat_id = {chat_id} AND user_id = {user_id};"
                )
        else:
            await self.insert_into_users(user_id)
            async with PostgresConnection() as connection:
                await connection.execute(f"INSERT INTO users_in_chats VALUES ({user_id}, {chat_id});")


class CommandGuesserMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if not self.event.text.startswith('!!') and not self.event.text.startswith('!'):
            return None
        custom_command = self.event.text.startswith('!!')
        if custom_command:
            text = self._convert_options()
        else:
            text = self._convert_command(self._convert_options())
            command = text.split(maxsplit=1)[0].lstrip('!')
            match = self._get_match(command.lower(), 2)
            if not match:
                return None
            text = text.replace(f"!{command}", f"!{match}")
        if self.event.text == text:
            return None
        if await has_postgres_data(f"SELECT * FROM users WHERE user_id = {self.event.from_id} AND autocorrect = false"):
            await self.event.answer(f"Возможно, вы имели ввиду <<{text}>>?")
            self.stop()
        else:
            self.event.text = text

    @staticmethod
    def _convert_command(text: str) -> str:
        cmd = text.split(maxsplit=1)[0]
        return text.replace(cmd, ''.join(keyboard.CYRILLIC.get(s, s) for s in cmd))

    def _convert_options(self) -> str:
        text = self.event.text
        for opt in re.findall(r'\s~~\S+', text):
            text = text.replace(opt, ''.join(keyboard.CYRILLIC.get(s, s) for s in opt))
        return text

    @lru_cache()
    def _calc_lev_dist(self, s1: str, s2: str) -> int:
        if len(s1) == 0 or len(s2) == 0:
            return len(s1) or len(s2)

        if s1[0] == s2[0]:
            return self._calc_lev_dist(s1[1:], s2[1:])

        return 1 + min(
            self._calc_lev_dist(s1[1:], s2),
            self._calc_lev_dist(s1, s2[1:]),
            self._calc_lev_dist(s1[1:], s2[1:])
        )

    def _get_match(self, cmd: str, min_dist: int) -> Optional[str]:
        matches = {self._calc_lev_dist(cmd, C): C for C in COMMANDS}
        return matches[min(matches)] if matches and min(matches) <= min_dist else None
