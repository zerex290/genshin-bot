import random
import os
import re
from dataclasses import dataclass
from typing import ClassVar

from vkbottle import Keyboard, KeyboardButtonColor, Callback
from vkbottle.bot import BotLabeler, Message, MessageEvent

from .base import RandomTag
from bot.src import Options, Payload
from bot.src.config import bot
from bot.src.parsers import SankakuParser
from bot.src.rules import CommandRule, EventRule
from bot.src.utils import find_forbidden_tags
from bot.src.utils.files import download, upload
from bot.src.constants import tags as t
from bot.src.errors import IncompatibleOptions
from bot.src.validators.default import *
from bot.src.manuals import default as man
from bot.src.types.sankaku import MediaType, Rating


bl = BotLabeler()


@dataclass()
class _RandomPictureState:
    PSEUDONYMS: ClassVar[dict[str, str]] = {v: k for k, v in RandomTag.get_all_tags().items()}
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

    def __init__(self, message: Message, options: Options, validator: RandomPictureValidator) -> None:
        self.message = message
        self.options = options
        self.validator = validator

    @staticmethod
    def get_interactive_keyboard(is_public: bool, user_id: int, state: str, msg_id: int) -> str:
        kb = Keyboard(inline=is_public)
        for i, values in enumerate(RandomPicture.SECTIONS.items()):
            button_type, label = values
            kb.add(
                Callback(
                    label,
                    {
                        'handler': RandomPicture.__name__,
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
                {'handler': RandomPicture.__name__, 'user_id': user_id, 'msg_id': msg_id, 'type': 'exit'}
            ),
            KeyboardButtonColor.NEGATIVE
        )
        return kb.get_json()

    @staticmethod
    async def get_attachments(tags: tuple[str, ...], nsfw: bool, search_limit: int, fav_count: int) -> str:
        attachments = []
        downloaded = []
        rating = Rating.E if nsfw else Rating.S
        async for post in SankakuParser(tags=tags, rating=rating).iter_posts(fav_count):
            if len(attachments) >= search_limit:
                break
            if post.id in downloaded:
                continue
            if post.mediatype != MediaType.IMAGE:
                continue
            if nsfw and find_forbidden_tags(post, ('loli', 'shota')):
                continue
            picture = await download(post.sample_url, name=f"{post.id}_{random.randint(0, 10000)}", ext=post.ext)
            if not picture:
                continue
            attachment = await upload(bot.group.api, 'photo_messages', picture)
            if attachment is not None:
                attachments.append(attachment)
                downloaded.append(post.id)
            os.remove(picture)
        return ','.join(attachments)

    async def get(self) -> None:
        state = await self._get_state(False)
        attachments = await self.get_attachments(*eval(repr(state)))
        await self.message.answer(self._compile_message(attachments), attachments)

    async def enter_interactive_mode(self) -> None:
        preload_msg = f"Вы вошли в интерактивный режим! Предзагрузка..."
        state = await self._get_state(True)
        msg = await self.message.answer(preload_msg)
        kb = self.get_interactive_keyboard(
            self.message.peer_id >= 2e9,
            self.message.from_id,
            repr(state),
            msg.conversation_message_id
        )
        await self.message.ctx_api.messages.edit(
            self.message.peer_id,
            re.sub(r'\sПред.+', f"\n\n{state}", preload_msg),
            keyboard=kb,
            conversation_message_id=msg.conversation_message_id
        )

    def _get_fav_count(self) -> int:
        fav_count = re.search(r'~~л\s\d+', self.message.text)
        self.validator.check_fav_count_defined(fav_count)
        fav_count = int(fav_count[0].split()[1])
        self.validator.check_fav_count_range(fav_count)
        return fav_count

    @staticmethod
    def _get_tags(text: list[str]) -> tuple[str, ...]:
        if len(text) > 1:
            return tuple(RandomTag.get_all_tags().get(tag, tag) for tag in text[1:])
        else:
            return ()

    @staticmethod
    def _compile_message(attachment_string: str) -> str:
        cases = {1: 'е', 2: 'я', 3: 'я', 4: 'я'}
        pictures = len(attachment_string.split(',')) if attachment_string else 0
        return f"По вашему запросу найдено {pictures} изображени{cases.get(pictures, 'й')}!"

    async def _get_state(self, is_interactive: bool) -> _RandomPictureState:
        state = []
        nsfw = True if '~~нсфв' in self.options else False
        if nsfw:
            await self.validator.check_user_is_don(bot.group.api, self.message.from_id)
        text = re.sub(r'^!пик\s?|~~нсфв|~~и|~~л\s\d+', '', self.message.text.lower()).split()
        self.validator.check_picture_quantity_specified(text)
        self.validator.check_picture_quantity(int(text[0]))
        chosen_tags = self._get_tags(text)
        self.validator.check_tag_quantity(chosen_tags, is_interactive)
        state.append(chosen_tags)
        state.append(nsfw)
        state.append(int(text[0]))
        if '~~л' in self.options:
            state.append(self._get_fav_count())
        return _RandomPictureState(*state)


@bl.message(CommandRule(['пик'], ['~~п', '~~нсфв', '~~л', '~~и'], man.RandomPicture))
async def get_random_picture(message: Message, options: Options) -> None:
    async with RandomPictureValidator(message) as validator:
        picture = RandomPicture(message, options, validator)
        if '~~п' in options:
            raise IncompatibleOptions(options)
        elif '~~и' in options:
            await picture.enter_interactive_mode()
        else:
            await picture.get()


@bl.raw_event('message_event', MessageEvent, EventRule(RandomPicture, ['menu']))
async def return_to_menu(event: MessageEvent, payload: Payload) -> None:
    state = _RandomPictureState(*eval(payload['state']))
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


@bl.raw_event('message_event', MessageEvent, EventRule(RandomPicture, ['exit']))
async def exit_interactive_mode(event: MessageEvent, payload: Payload) -> None:
    await event.ctx_api.messages.edit(
        event.peer_id,
        'Произведен выход из интерактивного режима.',
        keyboard=Keyboard().get_json(),
        conversation_message_id=payload['msg_id']
    )


@bl.raw_event('message_event', MessageEvent, EventRule(RandomPicture, [*list(RandomPicture.SECTIONS), 'search']))
async def get_section_objects(event: MessageEvent, payload: Payload) -> None:
    attachments = None
    if payload['type'] == 'search':
        payload['type'] = payload['prev']
        del payload['prev']
        state = _RandomPictureState(*eval(payload['state']))
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
                        'handler': RandomPicture.__name__,
                        'user_id': payload['user_id'],
                        'msg_id': payload['msg_id'],
                        'type': 'menu',
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
                        'handler': RandomPicture.__name__,
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
        _RandomPictureState(*eval(payload['state'])),
        RandomPicture.SECTIONS.get(payload['type'], payload['type']),
        payload.get('page', 0) + 1
    ]
    if payload.get('tag') is not None:
        msg_params.append(
            f"\n🕹Последний выбранный тег: "
            f"{_RandomPictureState.PSEUDONYMS.get(payload['tag'], payload['tag'])}"
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
