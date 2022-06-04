import traceback

from vkbottle.bot import Blueprint, Message

from bot.utils import PostgresConnection
from bot.rules import AdminRule


bp = Blueprint('AdminCommands')


class UnregisteredExceptions(Exception):
    pass


@bp.on.message(AdminRule(admins=(191901652, 687594282)))
async def execute(message: Message, postgres: bool) -> None:
    code: str = message.text.lstrip('!execpg').lstrip('!exec').lstrip()
    if not postgres:
        try:
            exec(f"async def _aexecute(message):" + ''.join([f"\n    {line}" for line in code.split('\n')]))
            await locals()['_aexecute'](message)
        except UnregisteredExceptions:
            exception = traceback.format_exc()
            exception = exception[-4096:] if len(exception) > 4096 else exception
            await message.answer(f"Ошибка: {exception}")
        return None

    async with PostgresConnection() as connection:
        try:
            exec(f"async def _aexecute(message, connection):" + ''.join([f"\n    {line}" for line in code.split('\n')]))
            await locals()['_aexecute'](message, connection)
        except UnregisteredExceptions:
            exception = traceback.format_exc()
            exception = exception[-4096:] if len(exception) > 4096 else exception
            await message.answer(f"Ошибка: {exception}")
