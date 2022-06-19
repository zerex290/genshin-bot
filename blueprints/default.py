import random
import os
from typing import Optional
from asyncio import sleep

from vkbottle.bot import Blueprint, Message

from bot.parsers import SankakuParser
from bot.rules import CommandRule
from bot.utils import PostgresConnection
from bot.utils.files import download, upload
from bot.src.constants import keyboard, tags
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.validators.default import *
from bot.src.manuals import default as man
from bot.src.types.sankaku import MediaType
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('DefaultCommands')


@bp.on.message(CommandRule(('команды',), options=('-п',)))
async def get_commands_article(message: Message, options: tuple[str, ...]) -> None:
    await message.answer(man.Guide.options[options[0]])


@bp.on.message(CommandRule(('автокоррект',), options=('-п', '-выкл', '-вкл')))
async def manage_syntax_autocorrection(message: Message, options: tuple[str, ...]) -> None:
    async with AutocorrectionValidator(message) as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.Autocorrection.options[options[0]])
            case ('-[default]',):
                async with PostgresConnection() as connection:
                    autocorrect = await connection.fetchrow(
                        f"SELECT autocorrect FROM users WHERE user_id = {message.from_id};"
                    )
                    autocorrect = dict(autocorrect)['autocorrect']
                await message.answer(f"У вас {'включена' if autocorrect else 'выключена'} автокоррекция команд!")
            case ('-выкл',):
                await validator.check_autocorrection_already_disabled(message.from_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE users SET autocorrect = false WHERE user_id = {message.from_id};"
                    )
                await message.answer('Автокоррекция команд теперь выключена!')
            case ('-вкл',):
                await validator.check_autocorrection_already_enabled(message.from_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE users SET autocorrect = true WHERE user_id = {message.from_id};"
                    )
                await message.answer('Автокоррекция команд теперь включена!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('выбери',), options=('-п',)))
async def choose(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.Choice.options:
        await message.answer(man.Choice.options[options[0]])
        return None

    async with ChoiceValidator(message) as validator:
        choice_options = message.text.lstrip('!выбери').split('/') if message.text.find('/') != -1 else []
        validator.check_choice_options_specified(choice_options)
        await message.answer(random.choice(choice_options))


@bp.on.message(CommandRule(('конверт',), options=('-п',)))
async def convert(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.Converter.options:
        await message.answer(man.Converter.options[options[0]])
        return None

    async with ConvertValidator(message) as validator:
        validator.check_reply_message(message.reply_message)
        validator.check_reply_message_text(message.reply_message.text)
        converted_message = ''.join([keyboard.CYRILLIC.get(symbol, symbol) for symbol in message.reply_message.text])
        await message.answer(converted_message)


def _evaluate_time(time: str) -> Optional[int]:
    try:
        time = time.replace('ч', '*3600+').replace('м', '*60+').replace('с', '*1+').strip().rpartition('+')
        countdown = eval(time[0])
    except (SyntaxError, NameError):
        countdown = None
    return countdown


@bp.on.message(CommandRule(('таймер',), options=('-п',)))
async def set_timer(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.Timer.options:
        await message.answer(man.Timer.options[options[0]])
        return None

    text = message.text.lstrip('!таймер')
    async with TimerValidator(message) as validator:
        validator.check_timer_specified(text)
        time, note = (text.split('/')[0], text.split('/')[1]) if text.find('/') != -1 else (text, '')
        countdown = _evaluate_time(time)
        validator.check_timer_syntax(countdown)
        await message.answer('Таймер установлен!')
        await sleep(countdown)
        response = (
            f"@id{message.from_id} ({(await message.get_user()).first_name}), время прошло! "
            f"{'Пометка: ' + note if note else ''}"
        )
        await message.answer(response)


@bp.on.message(CommandRule(('перешли',), options=('-п',)))
async def forward_attachments(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.Attachments.options:
        await message.answer(man.Attachments.options[options[0]])
        return None

    async with AttachmentForwardValidator(message) as validator:
        attachments = message.attachments
        validator.check_attachments(attachments)
        response = [f"photo{a.photo.owner_id}_{a.photo.id}_{a.photo.access_key}" for a in attachments if a.photo]
        validator.check_attachment_response(response)
        await message.answer(attachment=','.join(response))


def _get_all_tags() -> dict[str, str]:
    all_tags = {}
    all_tags.update(tags.GENSHIN_IMPACT)
    all_tags.update(tags.ART_STYLE)
    all_tags.update(tags.CLOTHING)
    all_tags.update(tags.JEWELRY)
    all_tags.update(tags.EMOTIONS)
    all_tags.update(tags.BODY)
    all_tags.update(tags.CREATURES)
    return all_tags


def _get_tag_groups(options: tuple[str, ...]) -> dict[str, str]:
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


def _randomize_tags(available_tags: dict[str, str]) -> list[str]:
    randomized_tags = []
    for _ in range(0, random.randint(1, len(available_tags) // 2)):
        if not available_tags:
            continue
        tag = random.choice(tuple(available_tags))
        randomized_tags.append(tag)
        del available_tags[tag]
    return randomized_tags


@bp.on.message(CommandRule(('рандомтег',), options=('-п', '-г', '-ср', '-о', '-у', '-э', '-т', '-с')))
async def get_random_tags(message: Message, options: tuple[str, ...]) -> None:
    async with BaseValidator(message):
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.RandomTag.options[options[0]])
            case ('-[default]',):
                await message.answer('\n'.join(_randomize_tags(_get_all_tags())))
            case _ if '-п' not in options:
                await message.answer('\n'.join(_randomize_tags(_get_tag_groups(options))))
            case _ if '-п' in options:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(('пик',), options=('-п',)))
async def get_random_picture(message: Message, options: tuple[str, ...]) -> None:
    if options[0] in man.RandomPicture.options:
        await message.answer(man.RandomPicture.options[options[0]])
        return None

    cases = {1: 'е', 2: 'я', 3: 'я', 4: 'я'}
    text = message.text.lstrip('!пик').split()
    async with RandomPictureValidator(message) as validator:
        validator.check_pictures_specified(text)
        validator.check_pictures_quantity(int(text[0]))
        all_tags = _get_all_tags()
        chosen_tags = tuple([all_tags.get(tag, tag) for tag in text[1:]]) if len(text) > 1 else ()
        validator.check_tags_quantity(chosen_tags)
        attachments = []
        parser = SankakuParser(tags=chosen_tags)
        async for post in parser.iter_posts():
            if len(attachments) >= int(text[0]):
                break
            if post.file_mediatype != MediaType.IMAGE:
                continue
            picture = await download(post.file_url, FILECACHE, str(post.id), post.file_suffix)
            if not picture:
                continue
            attachments.append(await upload(bp.api, 'photo_messages', picture))
            os.remove(picture)
        await message.answer(
            f"По вашему запросу найдено {len(attachments)} изображени{cases.get(len(attachments), 'й')}!",
            ','.join(attachments)
        )
