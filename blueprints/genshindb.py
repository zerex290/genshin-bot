import os
import re
from typing import Optional

from vkbottle import Keyboard, KeyboardButtonColor, Callback
from vkbottle.bot import Blueprint, Message, MessageEvent
from vkbottle_types.objects import MessagesKeyboard

from . import Options, Payload
from bot.parsers.honeyimpact import *
from bot.rules import CommandRule, EventRule
from bot.utils import PostgresConnection, json
from bot.errors import IncompatibleOptions
from bot.utils.files import download, upload
from bot.validators.genshindb import GenshinDBValidator
from bot.manuals import genshindb as man
from bot.imageprocessing.domains import get_domain_image
from bot.config.dependencies.paths import DATABASE_APPEARANCE, ASCENSION, FILECACHE


bp = Blueprint('GenshinDatabase')


class GenshinDatabase:
    SECTIONS = {
        'characters_type': 'Персонажи',
        'weapons_type': 'Оружие',
        'artifacts_type': 'Артефакты',
        'enemies_type': 'Противники',
        'books_type': 'Книги',
        'domains_type': 'Подземелья'
    }

    def __init__(self, message: Message, validator: GenshinDBValidator) -> None:
        self.message = message
        self.validator = validator

    async def _parse_shortcut_data(self) -> tuple[MessagesKeyboard, str, str]:
        reply_msg = (
            await self.message.ctx_api.messages.get_by_conversation_message_id(
                self.message.peer_id, [self.message.reply_message.conversation_message_id]
            )
        ).items[0]
        keyboard = reply_msg.keyboard
        delattr(keyboard, 'author_id')
        msg = reply_msg.text.replace("'", '"')
        photo = reply_msg.attachments[0].photo if reply_msg.attachments else None
        photo_id = f"photo{photo.owner_id}_{photo.id}" if photo else ''
        return keyboard, msg, photo_id

    def _change_keyboard_owner(self, keyboard: MessagesKeyboard) -> MessagesKeyboard:
        for b in keyboard.buttons:
            b[0]['action']['payload'] = re.sub(
                r'"user_id":\d+', f'"user_id":{self.message.from_id}', b[0]['action']['payload']
            )
        return keyboard

    async def _add_shortcut_to_db(self, shortcut: str, msg: str, photo_id: str, keyboard: MessagesKeyboard) -> None:
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO genshin_db_shortcuts VALUES (
                    {self.message.from_id}, $1, $2, '{photo_id}', '{keyboard.json()}'
                );
            """, shortcut, msg)

    async def add_shortcut(self) -> str:
        shortcut = self.message.text[self.message.text.find('~~аш') + 4:].strip()
        self.validator.check_shortcut_specified(shortcut)
        await self.validator.check_shortcut_new(shortcut, self.message.from_id)
        self.validator.check_reply_message(self.message.reply_message)
        keyboard, msg, photo_id = await self._parse_shortcut_data()
        self.validator.check_reply_message_keyboard(keyboard)
        keyboard = self._change_keyboard_owner(keyboard)
        await self._add_shortcut_to_db(shortcut, msg, photo_id, keyboard)
        return shortcut

    async def delete_shortcut(self) -> str:
        shortcut = self.message.text[self.message.text.find('~~дш') + 4:].strip()
        self.validator.check_shortcut_specified(shortcut)
        await self.validator.check_shortcut_exist(shortcut, self.message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                DELETE FROM genshin_db_shortcuts WHERE shortcut = $1 AND user_id = {self.message.from_id};
            """, shortcut)
        return shortcut

    async def get_user_shortcuts(self) -> str:
        await self.validator.check_shortcuts_created(self.message.from_id)
        async with PostgresConnection() as connection:
            shortcuts = await connection.fetch(
                f"SELECT shortcut FROM genshin_db_shortcuts WHERE user_id = {self.message.from_id};"
            )
            return 'Список ваших шорткатов:\n' + '\n'.join(dict(s)['shortcut'] for s in shortcuts)

    @staticmethod
    def _get_interactive_keyboard(user_id: int) -> str:
        kb = Keyboard(inline=True)
        for i, values in enumerate(GenshinDatabase.SECTIONS.items()):
            button_type, label = values
            kb.add(
                Callback(label, {'user_id': user_id, 'type': button_type}),
                KeyboardButtonColor.PRIMARY
            )
            if i + 1 != len(GenshinDatabase.SECTIONS):
                kb.row()
        return kb.get_json()

    @staticmethod
    async def get_main_menu(user_id: int) -> dict[str, str, str]:
        message = f"Доброго времени суток, {(await bp.api.users.get([user_id]))[0].first_name}!"
        attachment = await upload(bp.api, 'photo_messages', DATABASE_APPEARANCE + os.sep + 'menu.png')
        keyboard = GenshinDatabase._get_interactive_keyboard(user_id)
        return {'message': message, 'attachment': attachment, 'keyboard': keyboard}

    async def _fetch_shortcut_from_db(self, shortcut: str) -> dict[str, str | int]:
        async with PostgresConnection() as connection:
            shortcut = await connection.fetchrow(f"""
                SELECT message, photo_id, keyboard FROM genshin_db_shortcuts 
                WHERE user_id = {self.message.from_id} AND shortcut = $1;
            """, shortcut)
            return dict(shortcut)

    async def get(self) -> None:
        shortcut = re.sub(r'^!гдб\s?', '', self.message.text)
        if not shortcut:
            await self.message.answer(**(await self.get_main_menu(self.message.from_id)))
            return None
        await self.validator.check_shortcut_exist(shortcut, self.message.from_id)
        shortcut = await self._fetch_shortcut_from_db(shortcut)
        await self.message.answer(
            message=shortcut['message'],
            attachment=shortcut['photo_id'] if shortcut['photo_id'] else None,
            keyboard=shortcut['keyboard']
        )


async def get_attachment_icon(icon_path: str) -> Optional[str]:
    """
    Check if icon exists.
    If yes, then upload it to vk server and return formatted attachment string.
    """
    if not os.path.exists(icon_path):
        return None
    return await upload(bp.api, 'photo_messages', icon_path)


async def cache_icon(url: str) -> str:
    """Download image from specified url and preserve it in cache files.

    :param url: Link to image
    :return: Path to cached image
    """
    name, suffix = url.rsplit('/', maxsplit=1)[1].split('.')
    if not os.path.exists(os.path.join(FILECACHE, f"{name}.{suffix}")):
        await download(url, FILECACHE, name, suffix)
    return os.path.join(FILECACHE, f"{name}.{suffix}")


@bp.on.message(CommandRule(['гдб'], ['~~п', '~~аш', '~~дш', '~~ш'], man.GenshinDatabase))
async def get_genshin_database(message: Message, options: Options) -> None:
    async with GenshinDBValidator(message) as validator:
        genshin_db = GenshinDatabase(message, validator)
        match options:
            case ['~~[default]']:
                await genshin_db.get()
            case ['~~аш']:
                shortcut = await genshin_db.add_shortcut()
                await message.answer(f"Шорткат '{shortcut}' был успешно создан!")
            case ['~~дш']:
                shortcut = await genshin_db.delete_shortcut()
                await message.answer(f"Шорткат '{shortcut}' был успешно удален!")
            case ['~~ш']:
                await message.answer(await genshin_db.get_user_shortcuts())
            case _:
                raise IncompatibleOptions(options)


@bp.on.raw_event('message_event', MessageEvent, EventRule(['menu']))
async def return_to_menu(event: MessageEvent, payload: Payload) -> None:
    await event.edit_message(**(await GenshinDatabase.get_main_menu(payload['user_id'])))


@bp.on.raw_event('message_event', MessageEvent, EventRule(list(GenshinDatabase.SECTIONS)))
async def get_db_sections(event: MessageEvent, payload: Payload) -> None:
    keyboards = []
    kb = Keyboard(inline=True)
    pl_type = payload['type'].split('_')[0]
    sections = json.load(pl_type)
    apl = payload.copy()  #: additional payload
    apl['type'] = pl_type

    buttons = 0
    last = list(sections)[-1]
    for section in sections:
        apl['section'] = section
        apl['s_page'] = len(keyboards)
        kb.add(Callback(section, apl.copy()))
        buttons += 1
        if buttons % 2 == 0 and section != last:
            kb.row()
        elif buttons % 7 == 0 or section == last:
            page = len(keyboards)
            epl = payload.copy()  #: extra payload for page control buttons
            kb.row()
            if page != 0:
                epl['s_page'] = page - 1
                kb.add(Callback('Назад', epl.copy()), KeyboardButtonColor.PRIMARY)
            kb.add(
                Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}),
                KeyboardButtonColor.POSITIVE
            )
            if section != last:
                epl['s_page'] = page + 1
                kb.add(Callback('Далее', epl.copy()), KeyboardButtonColor.PRIMARY)
            keyboards.append(kb.get_json())
            kb = Keyboard(inline=True)
            buttons = 0

    await event.edit_message(
        'Пожалуйста, выберите интересующий вас раздел!',
        keyboard=keyboards[payload.get('s_page', 0)],
        attachment=await get_attachment_icon(f"{DATABASE_APPEARANCE}{os.sep}{pl_type}.png")
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule([s.split('_')[0] for s in GenshinDatabase.SECTIONS]))
async def get_section_objects(event: MessageEvent, payload: Payload) -> None:
    keyboards = []
    kb = Keyboard(inline=True)
    sections = json.load(payload['type'])[payload['section']]
    apl = payload.copy()  #: additional payload
    apl['type'] = payload['type'][:-1]

    buttons = 0
    last = list(sections)[-1]
    for obj in sections:
        apl['object'] = obj
        apl['o_page'] = len(keyboards)
        kb.add(Callback(obj, apl.copy()))
        buttons += 1
        if buttons % 2 == 0 and buttons % 6 != 0 and obj != last:
            kb.row()
        elif buttons % 6 == 0 or obj == last:
            page = len(keyboards)
            epl = payload.copy()  #: extra payload for page control buttons
            epl['type'] = f"{payload['type']}_type"
            del epl['section']
            if epl.get('o_page') is not None:
                del epl['o_page']
            kb.row()
            kb.add(Callback('К выбору раздела', epl.copy()), KeyboardButtonColor.POSITIVE)
            epl = payload.copy()
            kb.row()
            if page != 0:
                epl['o_page'] = page - 1
                kb.add(Callback('Назад', epl.copy()), KeyboardButtonColor.PRIMARY)
            kb.add(
                Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}),
                KeyboardButtonColor.POSITIVE
            )
            if obj != last:
                epl['o_page'] = page + 1
                kb.add(Callback('Далее', epl.copy()), KeyboardButtonColor.PRIMARY)
            keyboards.append(kb.get_json())
            kb = Keyboard(inline=True)
            buttons = 0

    await event.edit_message(f"Поиск по разделу '{payload['section']}'!", keyboard=keyboards[payload.get('o_page', 0)])


@bp.on.raw_event('message_event', MessageEvent, EventRule(['character']))
async def get_character(event: MessageEvent, payload: Payload) -> None:
    character = CharacterParser(payload['section'], payload['object'])
    buttons = {
        'information': ('Основная информация', character.get_information),
        'active_skills': ('Активные навыки', character.get_active_skills),
        'passive_skills': ('Пассивные навыки', character.get_passive_skills),
        'constellations': ('Созвездия', character.get_constellations),
        'ascension': ('Возвышение', upload)
    }
    kb = Keyboard(inline=True)
    apl = payload.copy()

    default = list(buttons)[0]
    for data in buttons:
        if data != payload.get('data', default):
            apl['data'] = data
            kb.add(Callback(buttons[data][0], apl.copy()))
            kb.row()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    del apl['data']
    kb.add(Callback('К списку персонажей', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    if payload.get('data', default) != 'ascension':
        attachment = await upload(bp.api, 'photo_messages', await cache_icon(character.icon))
        message = await buttons[payload.get('data', default)][1]()
    else:
        attachment = await get_attachment_icon(f"{ASCENSION}{os.sep}{character.href.split('_')[0]}.png")
        message = f"🖼Материалы возвышения персонажа '{payload['object']}':"

    await event.edit_message(message, attachment=attachment, keyboard=kb.get_json())


@bp.on.raw_event('message_event', MessageEvent, EventRule(['weapon']))
async def get_weapon(event: MessageEvent, payload: Payload) -> None:
    weapon = WeaponParser(payload['section'], payload['object'])
    buttons = {
        'information': ('Основная информация', weapon.get_information),
        'ability': ('Способность оружия', weapon.get_ability),
        'progression': ('Прогрессия', weapon.get_progression),
        'refinement': ('Пробуждение', weapon.get_refinement),
        'story': ('История', weapon.get_story)
    }
    kb = Keyboard(inline=True)
    apl = payload.copy()

    default = list(buttons)[0]
    for data in buttons:
        if data != payload.get('data', default):
            apl['data'] = data
            kb.add(Callback(buttons[data][0], apl.copy()))
            kb.row()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    del apl['data']
    kb.add(Callback('К списку оружия', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    await event.edit_message(
        await buttons[payload.get('data', default)][1](),
        attachment=await upload(bp.api, 'photo_messages', await cache_icon(weapon.icon)),
        keyboard=kb.get_json()
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule(['artifact']))
async def get_artifact(event: MessageEvent, payload: Payload) -> None:
    artifact = ArtifactParser(payload['section'], payload['object'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К списку артефактов', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    await event.edit_message(
        await artifact.get_information(),
        attachment=await upload(bp.api, 'photo_messages', await cache_icon(artifact.icon)),
        keyboard=kb.get_json()
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule(['enemie']))
async def get_enemy(event: MessageEvent, payload: Payload) -> None:
    enemy = EnemyParser(payload['section'], payload['object'])
    buttons = {
        'information': ('Основная информация', enemy.get_information),
        'progression': ('Прогрессия', enemy.get_progression)
    }
    kb = Keyboard(inline=True)
    apl = payload.copy()

    default = list(buttons)[0]
    for data in buttons:
        if data != payload.get('data', default):
            apl['data'] = data
            kb.add(Callback(buttons[data][0], apl.copy()))
            kb.row()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    del apl['data']
    kb.add(Callback('К списку противников', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    await event.edit_message(
        await buttons[payload.get('data', default)][1](),
        attachment=await upload(bp.api, 'photo_messages', await cache_icon(enemy.icon)),
        keyboard=kb.get_json()
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule(['book']))
async def get_book(event: MessageEvent, payload: Payload) -> None:
    book = BookParser(payload['section'], payload['object'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К оглавлению', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    icon = await upload(bp.api, 'photo_messages', await cache_icon(book.icon))
    message = await book.get_information()
    book = await book.save_book()
    book_path, book_name = book, book.rsplit(os.sep, maxsplit=1)[1]
    doc = await upload(bp.api, 'document_messages', book_name, book_path, peer_id=event.peer_id)
    os.remove(book_path)
    await event.edit_message(
        message,
        attachment=f"{icon},{doc}",
        keyboard=kb.get_json()
    )


@bp.on.raw_event('message_event', MessageEvent, EventRule(['domain']))
async def get_domain(event: MessageEvent, payload: Payload) -> None:
    domain = DomainParser(payload['section'], payload['object'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['object']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К списку подземелий', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(Callback('Меню', {'user_id': payload['user_id'], 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    await event.edit_message(
        await domain.get_information(),
        attachment=await get_attachment_icon(await get_domain_image(domain.icon, domain.monsters, domain.rewards)),
        keyboard=kb.get_json()
    )
