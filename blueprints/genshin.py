import os
from datetime import datetime

from vkbottle.bot import Blueprint, Message

from bot.rules import CommandRule
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.utils.files import upload
from bot.src.manuals import genshin as man
from bot.config.dependencies.paths import DAILY_MATERIALS, BOSS_MATERIALS, BOOKS, DUNGEONS


bp = Blueprint('GenshinCommands')


async def _get_material_attachments(options: list[str]) -> str:
    days = {'~~пн': 0, '~~вт': 1, '~~ср': 2, '~~чт': 3, '~~пт': 4, '~~сб': 5, '~~вс': 6}
    response = []
    for option in options:
        response.append(await upload(bp.api, 'photo_messages', os.path.join(DAILY_MATERIALS, f"{days[option]}.png")))
    return ','.join(response)


@bp.on.message(
    CommandRule(['фарм'], ['~~п', '~~пн', '~~вт', '~~ср', '~~чт', '~~пт', '~~сб', '~~вс'], man.DailyMaterials)
)
async def get_daily_materials(message: Message, options: list[str]) -> None:
    async with BaseValidator(message):
        match options:
            case ['~~[default]']:
                daily_materials = await upload(
                    bp.api, 'photo_messages', os.path.join(DAILY_MATERIALS, f"{datetime.now().weekday()}.png")
                )
                await message.answer(attachment=daily_materials)
            case _ if '~~п' not in options:
                await message.answer(attachment=await _get_material_attachments(options))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['таланты'], ['~~п'], man.BossMaterials))
async def get_boss_materials(message: Message) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOSS_MATERIALS))


@bp.on.message(CommandRule(['книги'], ['~~п'], man.Books))
async def get_books(message: Message) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', BOOKS))


@bp.on.message(CommandRule(['данжи'], ['~~п'], man.Dungeons))
async def get_dungeons(message: Message) -> None:
    await message.answer(attachment=await upload(bp.api, 'photo_messages', DUNGEONS))
