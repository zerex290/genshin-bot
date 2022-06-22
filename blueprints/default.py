import random
import os
import re
from typing import Optional
from asyncio import sleep

from vkbottle.bot import Blueprint, Message

from bot.parsers import SankakuParser
from bot.rules import CommandRule
from bot.utils import PostgresConnection
from bot.utils.postgres import has_postgres_data
from bot.utils.files import download, upload
from bot.src.constants import keyboard, tags
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.validators.default import *
from bot.src.manuals import default as man
from bot.src.types.sankaku import MediaType
from bot.config.dependencies.paths import FILECACHE


bp = Blueprint('DefaultCommands')


@bp.on.message(CommandRule(['команды'], ['~~п'], man.Guide))
async def get_commands_article(message: Message) -> None:
    commands = (
        'Статья с подробным описанием всех команд: vk.com/@bot_genshin-commands\n\n'
        'Основные команды:\n'
        '!команды\n'
        '!автокоррект\n'
        '!перешли\n'
        '!конверт\n'
        '!таймер\n'
        '!выбери\n'
        '!пик\n'
        '!рандомтег\n\n'
        'Команды по Геншину:\n'
        '!линк\n'
        '!анлинк\n'
        '!фарм\n'
        '!таланты\n'
        '!книги\n'
        '!данжи\n'
        '!гдб\n'
        '!заметки\n'
        '!резинноут\n'
        '!награды\n'
        '!статы\n'
        '!пром\n'
        '!дневник\n'
        '!бездна\n\n'
        'Пользовательские команды:\n'
        '!комы\n'
        '!аддком\n'
        '!делком\n'
        '!!<<триггер>>'
    )
    await message.answer(commands)


@bp.on.message(CommandRule(['автокоррект'], ['~~п', '~~выкл', '~~вкл'], man.Autocorrection))
async def manage_syntax_autocorrection(message: Message, options: list[str]) -> None:
    async with AutocorrectionValidator(message) as validator:
        match options:
            case ['~~[default]']:
                status = await has_postgres_data(
                    f"SELECT * FROM users WHERE user_id = {message.from_id} AND autocorrect = true;"
                )
                await message.answer(f"У вас {'включена' if status else 'выключена'} автокоррекция команд!")
            case ['~~выкл']:
                await validator.check_autocorrection_already_disabled(message.from_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE users SET autocorrect = false WHERE user_id = {message.from_id};"
                    )
                await message.answer('Автокоррекция команд теперь выключена!')
            case ['~~вкл']:
                await validator.check_autocorrection_already_enabled(message.from_id)
                async with PostgresConnection() as connection:
                    await connection.execute(
                        f"UPDATE users SET autocorrect = true WHERE user_id = {message.from_id};"
                    )
                await message.answer('Автокоррекция команд теперь включена!')
            case _:
                raise IncompatibleOptions(options)


@bp.on.message(CommandRule(['выбери'], ['~~п'], man.Choice))
async def choose(message: Message) -> None:
    async with ChoiceValidator(message) as validator:
        options = re.sub(r'^!выбери\s?', '', message.text).split('/') if message.text.find('/') != -1 else []
        validator.check_choice_options_specified(options)
        await message.answer(random.choice(options))


@bp.on.message(CommandRule(['конверт'], ['~~п'], man.Converter))
async def convert(message: Message) -> None:
    async with ConvertValidator(message) as validator:
        validator.check_reply_message(message.reply_message)
        validator.check_reply_message_text(message.reply_message.text)
        text = message.reply_message.text
        converted = ''.join(
            keyboard.CYRILLIC.get(s, keyboard.LATIN.get(s, s))
            if ord(s) < 128
            else keyboard.LATIN.get(s, keyboard.CYRILLIC.get(s, s))
            for s in message.reply_message.text
        )
        await message.answer(converted)


def _evaluate_time(time: str) -> Optional[int]:
    try:
        time = re.sub('[xч]', '*3600+', re.sub('[vм]', '*60+', re.sub('[cс]', '*1+', time))).strip().rpartition('+')
        countdown = eval(time[0])
    except (SyntaxError, NameError):
        countdown = None
    return countdown


@bp.on.message(CommandRule(['таймер'], ['~~п'], man.Timer))
async def set_timer(message: Message) -> None:
    async with TimerValidator(message) as validator:
        text = message.text.lstrip('!таймер')
        validator.check_timer_specified(text)
        time, note = (text.split('/')[0], text.split('/')[1]) if text.find('/') != -1 else (text, '')
        countdown = _evaluate_time(time.lower())
        validator.check_timer_syntax(countdown)
        await message.answer('Таймер установлен!')
        await sleep(countdown)
        response = (
            f"@id{message.from_id} ({(await message.get_user()).first_name}), время прошло! "
            f"{'Пометка: ' + note if note else ''}"
        )
        await message.answer(response)


@bp.on.message(CommandRule(['перешли'], ['~~п'], man.Attachments))
async def forward_attachments(message: Message) -> None:
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


def _get_tag_groups(options: list[str]) -> dict[str, str]:
    gathered_tags = {}
    tag_groups = {
        '~~г': tags.GENSHIN_IMPACT,
        '~~ср': tags.ART_STYLE,
        '~~о': tags.CLOTHING,
        '~~у': tags.JEWELRY,
        '~~э': tags.EMOTIONS,
        '~~т': tags.BODY,
        '~~с': tags.CREATURES
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


@bp.on.message(CommandRule(['рандомтег'], ['~~п', '~~г', '~~ср', '~~о', '~~у', '~~э', '~~т', '~~с'], man.RandomTag))
async def get_random_tags(message: Message, options: list[str]) -> None:
    async with BaseValidator(message):
        match options:
            case ['~~[default]']:
                await message.answer('\n'.join(_randomize_tags(_get_all_tags())))
            case _ if '~~п' not in options:
                await message.answer('\n'.join(_randomize_tags(_get_tag_groups(options))))
            case _ if '~~п' in options:
                raise IncompatibleOptions(options)


def _compile_message(attachments: list[str]) -> str:
    cases = {1: 'е', 2: 'я', 3: 'я', 4: 'я'}
    return f"По вашему запросу найдено {len(attachments)} изображени{cases.get(len(attachments), 'й')}!"


@bp.on.message(CommandRule(['пик'], ['~~п'], man.RandomPicture))
async def get_random_picture(message: Message) -> None:
    async with RandomPictureValidator(message) as validator:
        text = message.text.lstrip('!пик').split()
        validator.check_pictures_specified(text)
        validator.check_pictures_quantity(int(text[0]))
        chosen_tags = tuple(_get_all_tags().get(tag, tag) for tag in text[1:]) if len(text) > 1 else ()
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
        await message.answer(_compile_message(attachments), ','.join(attachments))
