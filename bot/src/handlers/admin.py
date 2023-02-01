import traceback

from vkbottle.bot import BotLabeler, Message

from ..utils import PostgresConnection
from ..rules import AdminRule
from ..config.dependencies import ADMINS


bl = BotLabeler()


@bl.message(AdminRule('exec', ADMINS))
async def execute(message: Message) -> None:
    code: str = message.text.lstrip('!exec').lstrip()
    # noinspection PyBroadException
    try:
        async with PostgresConnection() as connection:
            exec(
                f"async def aexec(message, connection):"
                + ''.join([f"\n    {line}" for line in code.split('\n')])
            )
            await locals()['aexec'](message, connection)
    except Exception:
        exc = traceback.format_exc()
        exc = exc[-4096:] if len(exc) > 4096 else exc
        await message.answer(f"Ошибка: {exc}")
