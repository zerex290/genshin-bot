import random
import os
import re
from dataclasses import dataclass
from typing import Optional, ClassVar
from asyncio import sleep

from vkbottle import Keyboard, KeyboardButtonColor, Callback
from vkbottle.bot import Blueprint, Message, MessageEvent

from bot.parsers import SankakuParser
from bot.rules import CommandRule, EventRule
from bot.utils import PostgresConnection, find_restricted_tags
from bot.utils.postgres import has_postgres_data
from bot.utils.files import download, upload
from bot.src.constants import keyboard, tags as t
from bot.errors import IncompatibleOptions
from bot.validators import BaseValidator
from bot.validators.default import *
from bot.src.manuals import default as man
from bot.src.types.sankaku import MediaType, Rating
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
    all_tags.update(t.GENSHIN_IMPACT)
    all_tags.update(t.ART_STYLE)
    all_tags.update(t.CLOTHING)
    all_tags.update(t.JEWELRY)
    all_tags.update(t.EMOTIONS)
    all_tags.update(t.BODY)
    all_tags.update(t.CREATURES)
    return all_tags


def _get_tag_groups(options: list[str]) -> dict[str, str]:
    gathered_tags = {}
    tag_groups = {
        '~~г': t.GENSHIN_IMPACT,
        '~~ср': t.ART_STYLE,
        '~~о': t.CLOTHING,
        '~~у': t.JEWELRY,
        '~~э': t.EMOTIONS,
        '~~т': t.BODY,
        '~~с': t.CREATURES
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


@dataclass()
class RandomPictureState:
    PSEUDONYMS: ClassVar[dict[str, str]] = {v: k for k, v in _get_all_tags().items()}
    tags: tuple[str, ...]
    nsfw: bool
    search_limit: int
    fav_count: int = 50

    def __repr__(self) -> str:
        response = [self.tags, self.nsfw, self.search_limit, self.fav_count]
        return repr(response)

    def __str__(self) -> str:
        tags = [self.PSEUDONYMS.get(tag, tag) for tag in self.tags]
        response = (
            f"⚙Ваши предохраненные настройки:\n"
            f"🔍Искомое кол-во изображений: {self.search_limit}\n"
            f"💜Установленное кол-во лайков: {self.fav_count}\n"
            f"🔞Режим NSFW: {'да' if self.nsfw else 'нет'}"
        )
        if tags:
            response += f"\n📃Теги: {' | '.join(tags)}"
        return response


class RandomPicture:
    SECTIONS = {
        'art_style': 'Стиль рисунка',
        'genshin_impact': 'Геншин',
        'creatures': 'Существа',
        'clothing': 'Одежда',
        'jewelry': 'Украшения',
        'emotions': 'Эмоции',
        'body': 'Тело'
    }

    def __init__(self, message: Message, options: list[str], validator: RandomPictureValidator) -> None:
        self._message = message
        self._options = options
        self._validator = validator

    def _get_fav_count(self) -> int:
        fav_count = re.search(r'~~л\s\d+', self._message.text)
        self._validator.check_fav_count_defined(fav_count)
        fav_count = int(fav_count[0].split()[1])
        self._validator.check_fav_count_range(fav_count)
        return fav_count

    @staticmethod
    def _get_tags(text: list[str]) -> tuple[str, ...]:
        if len(text) > 1:
            return tuple(_get_all_tags().get(tag, tag) for tag in text[1:])
        else:
            return ()

    @staticmethod
    def _compile_message(attachment_string: str) -> str:
        cases = {1: 'е', 2: 'я', 3: 'я', 4: 'я'}
        attachments = attachment_string.split(',')
        return f"По вашему запросу найдено {len(attachments)} изображени{cases.get(len(attachments), 'й')}!"

    @staticmethod
    def get_interactive_keyboard(is_public: bool, user_id: int, state: str, msg_id: int) -> str:
        kb = Keyboard(inline=is_public)
        for i, values in enumerate(RandomPicture.SECTIONS.items()):
            button_type, label = values
            kb.add(
                Callback(
                    label,
                    {
                        'user_id': user_id, 'msg_id': msg_id,
                        'type': button_type, 'state': state
                    }
                ),
                KeyboardButtonColor.PRIMARY
            )
            if i % 2 == 0:
                kb.row()
        kb.add(
                Callback(
                    'Выйти',
                    {'user_id': user_id, 'msg_id': msg_id, 'type': 'exit'}
                ),
                KeyboardButtonColor.NEGATIVE
            )
        return kb.get_json()

    @staticmethod
    async def get_attachments(tags: tuple[str, ...], nsfw: bool, search_limit: int, fav_count: int) -> str:
        attachments: list[str] = []
        rating = Rating.E if nsfw else Rating.S
        async for post in SankakuParser(tags=tags, rating=rating).iter_posts(fav_count):
            if len(attachments) >= search_limit:
                break
            if nsfw and find_restricted_tags(post, ('loli', 'shota')):
                continue
            if post.file_mediatype != MediaType.IMAGE:
                continue
            picture = await download(post.sample_url, FILECACHE, str(post.id), post.file_suffix)
            if not picture:
                continue
            attachment = await upload(bp.api, 'photo_messages', picture)
            if attachment is not None:
                attachments.append(attachment)
            os.remove(picture)
        return ','.join(attachments)

    async def _get_state(self, is_interactive: bool) -> RandomPictureState:
        state = []
        nsfw = True if '~~нсфв' in self._options else False
        if nsfw:
            await self._validator.check_user_is_don(bp.api, self._message.from_id)
        text = re.sub(r'^!пик\s?|~~нсфв|~~и|~~л\s\d+', '', self._message.text.lower()).split()
        self._validator.check_pictures_specified(text)
        self._validator.check_pictures_quantity(int(text[0]))
        chosen_tags = self._get_tags(text)
        self._validator.check_tags_quantity(chosen_tags, is_interactive)
        state.append(chosen_tags)
        state.append(nsfw)
        state.append(int(text[0]))
        if '~~л' in self._options:
            state.append(self._get_fav_count())
        return RandomPictureState(*state)

    async def get(self) -> None:
        state = await self._get_state(False)
        attachments = await self.get_attachments(*eval(repr(state)))
        await self._message.answer(self._compile_message(attachments), attachments)

    async def enter_interactive_mode(self) -> None:
        preload_msg = f"Вы вошли в интерактивный режим! Предзагрузка..."
        state = await self._get_state(True)
        msg = await self._message.answer(preload_msg)
        kb = self.get_interactive_keyboard(
            self._message.peer_id >= 2e9,
            self._message.from_id,
            repr(state),
            msg.conversation_message_id
        )
        await self._message.ctx_api.messages.edit(
            self._message.peer_id,
            re.sub(r'\sПред.+', f"\n\n{state}", preload_msg),
            keyboard=kb,
            conversation_message_id=msg.conversation_message_id
        )


@bp.on.message(CommandRule(['пик'], ['~~п', '~~нсфв', '~~л', '~~и'], man.RandomPicture))
async def get_random_picture(message: Message, options: list[str]) -> None:
    async with RandomPictureValidator(message) as validator:
        picture = RandomPicture(message, options, validator)
        if '~~п' in options:
            raise IncompatibleOptions(options)
        elif '~~и' in options:
            await picture.enter_interactive_mode()
        else:
            await picture.get()


@bp.on.raw_event('message_event', MessageEvent, EventRule(['main_menu']))
async def return_to_menu(event: MessageEvent, payload: dict[str, str | int]) -> None:
    state = RandomPictureState(*eval(payload['state']))
    await event.ctx_api.messages.edit(
        event.peer_id,
        str(state),
        keyboard=RandomPicture.get_interactive_keyboard(
            event.peer_id >= 2e9,
            payload['user_id'],
            repr(state),
            payload['msg_id']
        ),
        conversation_message_id=payload['msg_id']
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule(['exit']))
async def exit_from_tags_kb(event: MessageEvent, payload: dict[str, str | int]) -> None:
    await event.ctx_api.messages.edit(
        event.peer_id,
        'Произведен выход из интерактивного режима.',
        keyboard=Keyboard().get_json(),
        conversation_message_id=payload['msg_id']
    )


@bp.on.raw_event(
    'message_event',
    MessageEvent,
    EventRule(['art_style', 'genshin_impact', 'creatures', 'clothing', 'jewelry', 'emotions', 'body', 'search'])
)
async def get_tag_sections(event: MessageEvent, payload: dict[str, str | int]) -> None:
    attachments = None
    if payload['type'] == 'search':
        payload['type'] = payload['prev']
        del payload['prev']
        state = RandomPictureState(*eval(payload['state']))
        state.tags = (*state.tags, payload['tag'])
        attachments = await RandomPicture.get_attachments(*eval(repr(state)))

    keyboards = []
    kb = Keyboard(inline=event.peer_id >= 2e9)
    tag_group = getattr(t, payload['type'].upper())
    apl = payload.copy()  #: additional payload
    apl['prev'] = payload['type']
    apl['type'] = 'search'

    buttons = 0
    last = list(tag_group)[-1]
    for pseudonym, name_en in tag_group.items():
        apl['tag'] = name_en
        apl['page'] = len(keyboards)
        kb.add(Callback(pseudonym, apl.copy()))
        buttons += 1
        if buttons % 2 == 0 and buttons % 6 != 0 and pseudonym != last:
            kb.row()
        elif buttons % 6 == 0 or pseudonym == last:
            page = len(keyboards)
            kb.row()
            if page != 0:
                epl = payload.copy()  #: extra payload for page control buttons
                epl['page'] = page - 1
                kb.add(Callback('Назад', epl), KeyboardButtonColor.PRIMARY)
            kb.add(
                Callback(
                    'Меню',
                    {
                        'user_id': payload['user_id'],
                        'msg_id': payload['msg_id'],
                        'type': 'main_menu',
                        'state': payload['state']
                    }
                ),
                KeyboardButtonColor.POSITIVE
            )
            if pseudonym != last:
                epl = payload.copy()
                epl['page'] = page + 1
                kb.add(Callback('Далее', epl), KeyboardButtonColor.PRIMARY)
            kb.row()
            kb.add(
                Callback(
                    'Выйти',
                    {
                        'user_id': payload['user_id'],
                        'msg_id': payload['msg_id'],
                        'type': 'exit',
                    }
                ),
                KeyboardButtonColor.NEGATIVE
            )
            keyboards.append(kb.get_json())
            kb = Keyboard(inline=event.peer_id >= 2e9)
            buttons = 0

    msg = '{}\n📒Текущий раздел: {}\n📄Страница: {}{}{}'
    msg_params = [
        RandomPictureState(*eval(payload['state'])),
        RandomPicture.SECTIONS.get(payload['type'], payload['type']),
        payload.get('page', 0) + 1
    ]
    if payload.get('tag') is not None:
        msg_params.append(
            f"\n🕹Последний выбранный тег: "
            f"{RandomPictureState.PSEUDONYMS.get(payload['tag'], payload['tag'])}"
        )
    else:
        msg_params.append('')
    if attachments is not None:
        length = len(attachments.split(',')) if len(attachments) > 0 else 0
        msg_params.append(f"\n🕯Рез. последнего поиска: {length} изобр.")
    else:
        msg_params.append('')
    await event.ctx_api.messages.edit(
        event.peer_id,
        msg.format(*msg_params),
        attachment=attachments,
        keyboard=keyboards[payload.get('page', 0)],
        conversation_message_id=payload['msg_id']
    )
