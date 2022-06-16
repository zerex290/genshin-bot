import traceback

from vkbottle.bot import Blueprint, Message

from bot.utils import PostgresConnection
from bot.rules import AdminRule


bp = Blueprint('AdminCommands')


class UnregisteredException(Exception):
    pass


@bp.on.message(AdminRule(admins=(191901652, 687594282)))
async def execute(message: Message, postgres: bool) -> None:
    code: str = message.text.lstrip('!execpg').lstrip('!exec').lstrip()
    try:
        if postgres:
            async with PostgresConnection() as connection:
                exec(
                    f"async def _aexecute(message, connection):"
                    + ''.join([f"\n    {line}" for line in code.split('\n')])
                )
                await locals()['_aexecute'](message, connection)
        else:
            exec(
                f"async def _aexecute(message):"
                + ''.join([f"\n    {line}" for line in code.split('\n')])
            )
            await locals()['_aexecute'](message)
    except UnregisteredException:
        exc = traceback.format_exc()
        exc = exc[-4096:] if len(exc) > 4096 else exc
        await message.answer(f"Ошибка: {exc}")
