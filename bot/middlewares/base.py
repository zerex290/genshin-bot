import os

from vkbottle import BaseMiddleware
from vkbottle.bot import Message
from vkbottle_types.objects import MessagesMessageActionStatus, UsersUserFull

from bot.utils import PostgresConnection, get_timestamp_from_unix
from bot.utils.files import write_logs
from bot.utils.postgres import has_postgres_data
from bot.config.dependencies.paths import USER_COMMANDS


ACTIONS = [
    MessagesMessageActionStatus.CHAT_INVITE_USER,
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_MESSAGE_REQUEST,
    MessagesMessageActionStatus.CHAT_INVITE_USER_BY_LINK,
    MessagesMessageActionStatus.CHAT_KICK_USER
]


async def _insert_into_users(user: UsersUserFull) -> None:
    if await has_postgres_data(f"SELECT user_id FROM users WHERE user_id = {user.id};"):
        return None
    async with PostgresConnection() as connection:
        await connection.execute(f"""
                    INSERT INTO users VALUES (
                        {user.id}, '{user.first_name}', '{user.last_name}', false
                    );
                """)


async def _insert_into_users_in_chats(event, users: list, chat_id: int) -> None:
    chat_id = chat_id
    resin_notifications = 'false'
    async with PostgresConnection() as connection:
        for user in users:
            if user.member_id >= 0:
                invited_by = user.invited_by
                join_date = get_timestamp_from_unix(3, user.join_date)
                user_id = user.member_id
                await _insert_into_users((await event.ctx_api.users.get())[0])
                await connection.execute(f"""
                    INSERT INTO users_in_chats VALUES (
                        {user_id}, {chat_id}, '{join_date}', {invited_by}, '{resin_notifications}'
                    );
                """)


class GroupFilterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if self.event.from_id < 0:
            self.stop()


class CustomCommandsMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if not os.path.isdir(f"{USER_COMMANDS}{os.sep}{self.event.peer_id}{os.sep}") and self.event.peer_id >= 2e9:
            os.mkdir(f"{USER_COMMANDS}{os.sep}{self.event.peer_id}{os.sep}")


class UserRegisterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if self.event.from_id < 0:  #: Filter groups from inserting into database
            return None
        await _insert_into_users(await self.event.get_user())


class ChatRegisterMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if (self.event.peer_id < 2e9
                or await has_postgres_data(f"SELECT chat_id FROM chats WHERE chat_id = {self.event.peer_id}")):
            return None
        chat = await self.event.ctx_api.messages.get_conversation_members(self.event.peer_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO chats VALUES (
                    {self.event.peer_id}, {chat.count}, true
                );
            """)
        await _insert_into_users_in_chats(self.event, chat.items, self.event.peer_id)


class ChatUsersUpdateMiddleware(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if not self.event.action or self.event.action.type not in ACTIONS:
            return None
        match self.event.action.type:
            case MessagesMessageActionStatus.CHAT_KICK_USER:
                async with PostgresConnection() as connection:
                    await connection.execute(f"""
                        DELETE FROM users_in_chats 
                        WHERE chat_id = {self.event.peer_id} AND user_id = {self.event.action.member_id};
                    """)
                    await connection.execute(f"""
                        UPDATE chats SET member_count = member_count - 1 WHERE chat_id = {self.event.peer_id};
                    """)
            case _:
                users = (await self.event.ctx_api.messages.get_conversation_members(self.event.peer_id)).items
                user_id = self.event.action.member_id
                chat_id = self.event.peer_id
                invited_by = None
                join_date = None
                resin_notifications = 'false'
                for user in users:
                    if user.member_id == user_id and user.member_id > 0:
                        invited_by = user.invited_by
                        join_date = get_timestamp_from_unix(3, user.join_date)
                async with PostgresConnection() as connection:
                    await connection.execute(f"""
                        INSERT INTO users_in_chats VALUES (
                            {user_id}, {chat_id}, '{join_date}', {invited_by}, '{resin_notifications}'
                        );
                    """)
                    await connection.execute(f"""
                        UPDATE chats SET member_count = member_count + 1 WHERE chat_id = {self.event.peer_id};
                    """)


class MessageLogMiddleware(BaseMiddleware[Message]):
    async def post(self) -> None:
        if not self.handlers:
            return None
        await write_logs(self.event, self.handlers)
