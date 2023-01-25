import traceback

from vkbottle.bot import Blueprint, Message

from bot.utils import PostgresConnection
from bot.rules import AdminRule
from bot.config.dependencies import ADMINS


bp = Blueprint('AdminCommands')


class UnregisteredException(Exception):
    pass


@bp.on.message(AdminRule('exec', ADMINS))
async def execute(message: Message) -> None:
    code: str = message.text.lstrip('!exec').lstrip()
    try:
        async with PostgresConnection() as connection:
            exec(
                f"async def aexec(message, connection):"
                + ''.join([f"\n    {line}" for line in code.split('\n')])
            )
            await locals()['aexec'](message, connection)
    except UnregisteredException:
        exc = traceback.format_exc()
        exc = exc[-4096:] if len(exc) > 4096 else exc
        await message.answer(f"Ошибка: {exc}")
