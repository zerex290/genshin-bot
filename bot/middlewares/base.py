import re
from typing import Optional
from functools import lru_cache

from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle_types.objects import MessagesMessageActionStatus

from bot.utils import PostgresConnection
from bot.utils.postgres import has_postgres_data
from bot.src.constants import keyboard, COMMANDS


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


class GroupFilterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if self.event.from_id < 0:
            self.stop()


class UserRegisterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if self.event.from_id < 0:  #: Filter groups from inserting into database
            return None
        await _insert_into_users(self.event.from_id)


class ChatRegisterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        chat_id = self.event.peer_id
        if chat_id < 2e9 or await has_postgres_data(f"SELECT * FROM chats WHERE chat_id = {chat_id}"):
            return None
        async with PostgresConnection() as connection:
            await connection.execute(f"INSERT INTO chats VALUES ({chat_id});")


class ChatUserUpdateMiddleware(BaseMiddleware[Message]):
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
        match self.event.action.type:
            case MessagesMessageActionStatus.CHAT_KICK_USER:
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"DELETE FROM users_in_chats WHERE chat_id = {chat_id} AND user_id = {user_id};"
                    )
            case _:
                await _insert_into_users(user_id)
                async with PostgresConnection() as connection:
                    await connection.execute(f"INSERT INTO users_in_chats VALUES ({user_id}, {chat_id});")


class CommandGuesserMiddleware(BaseMiddleware[Message]):
    def _format_text(self) -> str:
        text = self.event.text
        cmd = text.split(maxsplit=1)[0]
        opt = re.findall(r'\s~~\S+', text)
        text = text.replace(cmd, ''.join(keyboard.CYRILLIC.get(s, s) for s in cmd))
        for o in opt:
            text = text.replace(o, ''.join(keyboard.CYRILLIC.get(s, s) for s in o))
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

    async def pre(self) -> None:
        if not self.event.text.startswith('!') or self.event.text.startswith('!!'):
            return None
        text = self._format_text()
        command = text.split(maxsplit=1)[0].lstrip('!')
        match = self._get_match(command.lower(), 2)
        if not match:
            return None
        text = text.replace(f"!{command}", f"!{match}")
        if self.event.text == text:
            return None
        if await has_postgres_data(f"SELECT * FROM users WHERE user_id = {self.event.from_id} AND autocorrect = false"):
            await self.event.answer(f"~~Возможно, вы имели ввиду <<{text}>>?")
            self.stop()
        else:
            self.event.text = text


async def _insert_into_users(user_id: int) -> None:
    if await has_postgres_data(f"SELECT user_id FROM users WHERE user_id = {user_id};"):
        return None
    async with PostgresConnection() as connection:
        await connection.execute(f"INSERT INTO users VALUES ({user_id});")
