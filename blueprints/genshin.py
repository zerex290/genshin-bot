from typing import Tuple
from datetime import datetime

from vkbottle.bot import Blueprint, Message

from bot.rules import CommandRule
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.validators.genshin import *
from bot.utils.files import upload
from bot.utils.genshin import Paths
from bot.src.types.help import genshin as hints
from bot.src.types.genshin import Characters


bp = Blueprint('GenshinCommands')


async def _get_material_attachments(options: Tuple[str, ...]) -> str:
    days = {'-пн': 0, '-вт': 1, '-ср': 2, '-чт': 3, '-пт': 4, '-сб': 5, '-вс': 6}
    response = []
    for option in options:
        response.append(await upload(bp.api, 'photo_messages', Paths.get_daily_materials_path(days[option])))
    return ','.join(response)


@bp.on.message(CommandRule(('фарм',), options=('-п', '-пн', '-вт', '-ср', '-чт', '-пт', '-сб', '-вс')))
async def get_daily_materials(message: Message, options: Tuple[str, ...]) -> None:
    async with BaseValidator(message):
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(hints.DailyMaterials.slots.value[options[0]])
            case ('-[default]',):
                mats = await upload(bp.api, 'photo_messages', Paths.get_daily_materials_path(datetime.now().weekday()))
                await message.answer(attachment=mats)
            case _ if '-п' not in options:
                await message.answer(attachment=await _get_material_attachments(options))
            case _ if '-п' in options:
                raise IncompatibleOptions(options)


def _format_character_name(character: str) -> str:
    sub = {
        'хутао': 'Ху Тао',
        'ганьюй': 'Гань Юй',
        'чжунли': 'Чжун Ли',
        'синьянь': 'Синь Янь',
        'кэцин': 'Кэ Цин',
        'цици': 'Ци Ци',
        'чуньюнь': 'Чунь Юнь',
        'нингуан': 'Нин Гуан',
        'синцю': 'Син Цю',
        'бейдоу': 'Бей Доу',
        'сянлин': 'Сян Лин',
        'яньфэй': 'Янь Фэй',
        'юньцзинь': 'Юнь Цзинь',
        'шэньхэ': 'Шэнь Хэ',
        'елань': 'Е Лань',
        'кукисинобу': 'Куки Синобу',
        'синобу': 'Куки Синобу',
        'куки': 'Куки Синобу',
        'яэмико': 'Яэ Мико'
    }
    return sub.get(character, character.capitalize())


@bp.on.message(CommandRule(('ресы',), options=('-п',)))
async def get_ascension_materials(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.AscensionMaterials.slots.value:
        await message.answer(hints.AscensionMaterials.slots.value[options[0]])
        return None

    character = _format_character_name(message.text.lstrip('!ресы').lstrip().lower().replace(' ', ''))
    async with AscensionValidator(message) as validator:
        validator.check_character_specified(character)
        validator.check_character_available(character)
        validator.check_character_exists(character)
        ascension_materials = await upload(
            bp.api, 'photo_messages', Paths.get_ascension_path(Characters(character).name.lower())
        )
        await message.answer(attachment=ascension_materials)


@bp.on.message(CommandRule(('таланты',), options=('-п',)))
async def get_boss_materials(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.BossMaterials.slots.value:
        await message.answer(hints.BossMaterials.slots.value[options[0]])
        return

    boss_materials = await upload(bp.api, 'photo_messages', Paths.get_boss_materials_path())
    await message.answer(attachment=boss_materials)


@bp.on.message(CommandRule(('книги',), options=('-п',)))
async def get_books(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.Books.slots.value:
        await message.answer(hints.Books.slots.value[options[0]])
        return

    books = await upload(bp.api, 'photo_messages', Paths.get_books_path())
    await message.answer(attachment=books)


@bp.on.message(CommandRule(('данжи',), options=('-п',)))
async def get_domains(message: Message, options: Tuple[str, ...]) -> None:
    if options[0] in hints.Domains.slots.value:
        await message.answer(hints.Domains.slots.value[options[0]])
        return

    domains = await upload(bp.api, 'photo_messages', Paths.get_domains_path())
    await message.answer(attachment=domains)
