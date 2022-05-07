import random
import os
from typing import Optional, Tuple, List, Dict
from asyncio import sleep

from vkbottle.bot import Blueprint, Message

from bot.parsers import SankakuParser
from bot.rules import CommandRule
from bot.utils import PostgresConnection
from bot.utils.files import download, upload
from bot.errors.default import RandomPictureException
from bot.validators.default import RandomPictureValidator
from bot.src.constants import KEYBOARD, tags
from bot.src.types.help import default as hints
from bot.src.types.sankaku import MediaType
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('DefaultCommands')


@bp.on.message(CommandRule(('команды',), options=('-[default]', '-[error]', '-п')))
async def get_guide(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    await message.answer(hints.Guide.slots.value[options[0]])


@bp.on.message(CommandRule(('выбери',), options=('-[default]', '-[error]', '-п')))
async def choose(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.Choice.slots.value:
        await message.answer(hints.Choice.slots.value[options[0]])
        return None

    choice = random.choice(message.text.lstrip('!выбери').split('/')) if message.text.find('/') != -1 else ''
    await message.answer(choice) if choice else await message.answer('Ошибка: не указаны варианты для выбора!')


@bp.on.message(CommandRule(('конверт',), options=('-[default]', '-[error]', '-п')))
async def convert(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.Converter.slots.value:
        await message.answer(hints.Converter.slots.value[options[0]])
        return None

    if not message.reply_message:
        await message.answer('Ошибка: вы не прикрепили сообщение, текст которого нужно конвертировать!')
        return None
    if not message.reply_message.text:
        await message.answer('Ошибка: сообщение, которое вы прикрепили, не содержит текста!')
        return None
    converted_message = ''.join([KEYBOARD.get(symbol, symbol) for symbol in message.reply_message.text])
    await message.answer(converted_message)


def _evaluate_time(time: str) -> Optional[int]:
    try:
        time = time.replace('ч', '*3600+').replace('м', '*60+').replace('с', '*1+').strip().rpartition('+')
        countdown = eval(time[0])
    except (SyntaxError, NameError):
        countdown = None
    return countdown


@bp.on.message(CommandRule(('таймер',), options=('-[default]', '-[error]', '-п')))
async def set_timer(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.Timer.slots.value:
        await message.answer(hints.Timer.slots.value[options[0]])
        return None

    text = message.text.lstrip('!таймер')
    if not text:
        await message.answer('Ошибка: не задано время для установки таймера!')
        return None

    time, note = (text.split('/')[0], text.split('/')[1]) if text.find('/') != -1 else (text, '')
    countdown = _evaluate_time(time)
    if not countdown:
        await message.answer('Ошибка: Синтаксис команды нарушен!')
        return None

    await message.answer('Таймер установлен!')
    await sleep(countdown)

    async with PostgresConnection() as connection:
        query = await connection.fetchrow(f"SELECT first_name FROM users WHERE user_id = {message.from_id}")
        first_name = dict(query)['first_name']
        response = f"@id{message.from_id} ({first_name}), время прошло! {'Пометка: ' + note if note else ''}"
        await message.answer(response)


@bp.on.message(CommandRule(('перешли',), options=('-[default]', '-[error]', '-п')))
async def forward_attachments(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.Attachments.slots.value:
        await message.answer(hints.Attachments.slots.value[options[0]])
        return None

    if not message.attachments:
        await message.answer('Ошибка: не прикреплены изображения для пересылки!')
        return None

    response: List[str] = []
    for attachment in message.attachments:
        if not attachment.photo:
            continue
        response.append(f"photo{attachment.photo.owner_id}_{attachment.photo.id}_{attachment.photo.access_key}")
    if not response:
        await message.answer('Ошибка: пересылать можно только изображения!')
        return None
    await message.answer(attachment=','.join(response))


def _get_all_tags() -> Dict[str, str]:
    all_tags = {}
    all_tags.update(tags.GENSHIN_IMPACT)
    all_tags.update(tags.ART_STYLE)
    all_tags.update(tags.CLOTHING)
    all_tags.update(tags.JEWELRY)
    all_tags.update(tags.EMOTIONS)
    all_tags.update(tags.BODY)
    all_tags.update(tags.CREATURES)
    return all_tags


def _gather_available_tags(options: Tuple[str, ...]) -> Dict[str, str]:
    gathered_tags = {}
    tag_groups = {
        '-г': tags.GENSHIN_IMPACT,
        '-ср': tags.ART_STYLE,
        '-о': tags.CLOTHING,
        '-у': tags.JEWELRY,
        '-э': tags.EMOTIONS,
        '-т': tags.BODY,
        '-с': tags.CREATURES
    }
    for option in options:
        tag_group = tag_groups[option]
        for tag in tag_group:
            gathered_tags[tag] = tag_group[tag]
    return gathered_tags


def _choose_available_tags(available_tags: Dict[str, str]) -> List[str]:
    chosen_tags = []
    for _ in range(0, random.randint(1, len(available_tags) // 2)):
        if not available_tags:
            continue
        tag = random.choice(tuple(available_tags))
        chosen_tags.append(tag)
        del available_tags[tag]
    return chosen_tags


@bp.on.message(
    CommandRule(('рандомтег',), options=('-[default]', '-[error]', '-п', '-г', '-ср', '-о', '-у', '-э', '-т', '-с'))
)
async def get_random_tags(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    match options:
        case ('-[error]',) | ('-п',):
            await message.answer(hints.RandomTag.slots.value[options[0]])
        case ('-[default]',):
            await message.answer('\n'.join(_choose_available_tags(_get_all_tags())))
        case _ if '-п' not in options:
            await message.answer('\n'.join(_choose_available_tags(_gather_available_tags(options))))
        case _ if '-п' in options:
            await message.answer('Ошибка: вы не можете указать опцию -п в связке с остальными опциями!')


@bp.on.message(CommandRule(('пик',), options=('-[default]', '-[error]', '-п')))
async def get_random_picture(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.RandomPicture.slots.value:
        await message.answer(hints.RandomPicture.slots.value[options[0]])
        return None

    validator = RandomPictureValidator()
    query = message.text.lstrip('!пик').split()
    try:
        validator.check_quantity_specified(query)
        validator.check_quantity_overflowed(int(query[0]))
        all_tags = _get_all_tags()
        chosen_tags = tuple([all_tags.get(tag, tag) for tag in query[1:]]) if len(query) > 1 else ()
        validator.check_tags_overflowed(chosen_tags)
        attachments = []
        parser = SankakuParser(tags=chosen_tags)
        async for post in parser.iter_posts():
            if len(attachments) >= int(query[0]):
                break
            if post.file_mediatype != MediaType.IMAGE:
                continue
            file = await download(post.file_url, FILECACHE, str(post.id), post.file_suffix)
            if not file:
                continue
            attachments.append(await upload(bp.api, 'photo_messages', file))
            os.remove(file)
        await message.answer(f"По вашему запросу найдено {len(attachments)} изображений!", ','.join(attachments))
    except RandomPictureException as rp:
        await message.answer(rp.error)
