from . import PostgresConnection
from ..models.customcommands import CustomCommand


async def get_custom_commands(chat_id: int) -> list[CustomCommand]:
    async with PostgresConnection() as connection:
        commands = await connection.fetch(f"SELECT * FROM custom_commands WHERE chat_id = {chat_id};")
        return [CustomCommand(*dict(command).values()) for command in commands]
