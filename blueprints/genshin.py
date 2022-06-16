import os
from datetime import datetime

from vkbottle.bot import Blueprint, Message

from bot.rules import CommandRule
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.utils.files import upload
from bot.src.types.help import genshin as hints
from bot.config.dependencies.paths import DAILY_MATERIALS, BOSS_MATERIALS, BOOKS, DUNGEONS


bp = Blueprint('GenshinCommands')


async def _get_material_attachments(options: tuple[str, ...]) -> str:
    days = {'-пн': 0, '-вт': 1, '-ср': 2, '-чт': 3, '-пт': 4, '-сб': 5, '-вс': 6}
    response = []
    for option in options:
        response.append(await upload(bp.api, 'photo_messages', os.path.join(DAILY_MATERIALS, f"{days[option]}.png")))
    return ','.join(response)


@bp.on.message(CommandRule(('фарм',), options=('-п', '-пн', '-вт', '-ср', '-чт', '-пт', '-сб', '-вс')))
async def get_daily_materials(message: Message, options: tuple[str, ...]) -> None:
    async with BaseValidator(message):
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(hints.DailyMaterials.slots.value[options[0]])
            case ('-[default]',):
                materials = await upload(
                    bp.api, 'photo_messages', os.path.join(DAILY_MATERIALS, f"{datetime.now().weekday()}.png")
                )
                await message.answer(attachment=materials)
            case _ if '-п' not in options:
                await message.answer(attachment=await _get_material_attachments(options))
            case _ if '-п' in options:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('таланты',), options=('-п',)))
async def get_boss_materials(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in hints.BossMaterials.slots.value:
        await message.answer(hints.BossMaterials.slots.value[options[0]])
        return

    boss_materials = await upload(bp.api, 'photo_messages', BOSS_MATERIALS)
    await message.answer(attachment=boss_materials)


@bp.on.message(CommandRule(('книги',), options=('-п',)))
async def get_books(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in hints.Books.slots.value:
        await message.answer(hints.Books.slots.value[options[0]])
        return

    books = await upload(bp.api, 'photo_messages', BOOKS)
    await message.answer(attachment=books)


@bp.on.message(CommandRule(('данжи',), options=('-п',)))
async def get_dungeons(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in hints.Domains.slots.value:
        await message.answer(hints.Domains.slots.value[options[0]])
        return

    dungeons = await upload(bp.api, 'photo_messages', DUNGEONS)
    await message.answer(attachment=dungeons)
