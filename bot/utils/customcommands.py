from bot.utils.postgres import PostgresConnection
from bot.src.models.customcommands import CustomCommand, ChatCustomCommands


async def get_custom_commands(chat_id: int) -> ChatCustomCommands:
    async with PostgresConnection() as connection:
        commands = await connection.fetch(f"""
            SELECT name, creator_id, date_added AS _date, times_used, message, document_id, audio_id, photo_id 
            FROM custom_commands WHERE chat_id = {chat_id};
        """)
        return ChatCustomCommands(chat_id, [CustomCommand(**dict(command)) for command in commands])
