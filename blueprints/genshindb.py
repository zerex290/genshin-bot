import os
import re
from typing import Optional

from vkbottle import Keyboard, KeyboardButtonColor, Callback, GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent
from vkbottle_types.objects import MessagesKeyboard

from . import Options, Payload
from bot.parsers import CharacterParser, WeaponParser, ArtifactParser, EnemyParser, BookParser, DomainParser
from bot.rules import CommandRule, EventRule
from bot.utils import PostgresConnection, json
from bot.errors import IncompatibleOptions
from bot.utils.files import upload
from bot.validators.genshindb import GenshinDBValidator
from bot.manuals import genshindb as man
from bot.imageprocessing.domains import get_domain_image
from bot.config.dependencies.paths import DATABASE_APPEARANCE, ASCENSION


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
                Callback(label, {'user_id': user_id, 'type': button_type, 'page': 0}),  #: remove page later
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


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['menu']))
async def return_to_menu(event: MessageEvent, payload: Payload) -> None:
    await event.edit_message(**(await GenshinDatabase.get_main_menu(payload['user_id'])))


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    EventRule(['characters_type', 'weapons_type', 'artifacts_type', 'enemies_type', 'books_type', 'domains_type'])
)
async def get_type_filters(event: MessageEvent, payload: Payload) -> None:
    payload_type = payload['type'].split('_')[0]
    page = 0
    buttons = 0
    filters = json.load(payload_type)

    keyboards: list[str] = []
    keyboard = Keyboard(one_time=False, inline=True)

    for i, f in enumerate(filters):
        if buttons < 6 and f != list(filters)[-1]:
            if buttons % 2 == 0 and buttons > 0:
                keyboard.row()
            keyboard.add(
                Callback(f, {'user_id': event.user_id, 'type': payload_type, 'filter': f, 'page': 0}),
                KeyboardButtonColor.SECONDARY
            )
            buttons += 1
        else:
            keyboard.row()
            keyboard.add(
                Callback(f, {'user_id': event.user_id, 'type': payload_type, 'filter': f, 'page': 0}),
                KeyboardButtonColor.SECONDARY
            )
            keyboard.row()
            if page != 0:
                keyboard.add(
                    Callback('Назад', {'user_id': event.user_id, 'type': payload['type'], 'page': page - 1}),
                    KeyboardButtonColor.PRIMARY
                )
            keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
            if len(filters)-(i + 1) > 0:
                keyboard.add(Callback('Далее', {'user_id': event.user_id, 'type': payload['type'], 'page': page + 1}))
                page += 1
            buttons = 0
            keyboards.append(keyboard.get_json())
            keyboard = Keyboard(one_time=False, inline=True)

    await event.edit_message(
        'Пожалуйста, выберите интересующий вас раздел!',
        keyboard=keyboards[payload['page']],
        attachment=await get_attachment_icon(f"{DATABASE_APPEARANCE}{os.sep}{payload_type}.png")
    )


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    EventRule(['characters', 'weapons', 'artifacts', 'enemies', 'books', 'domains'])
)
async def get_filtered_objects(event: MessageEvent, payload: Payload) -> None:
    page = 0
    buttons = 0
    objects = json.load(payload['type'])[payload['filter']]

    keyboards: list[str] = []
    keyboard = Keyboard(one_time=False, inline=True)

    for i, obj in enumerate(objects):
        if buttons < 5 and obj != list(objects)[-1]:
            if buttons % 2 == 0 and buttons > 0:
                keyboard.row()
            keyboard.add(
                Callback(
                    obj,
                    {
                        'user_id': event.user_id, 'type': payload['type'][:-1],
                        'filter': payload['filter'], 'page': page, 'obj': obj, 'obj_data': 'information'
                    }
                ),
                KeyboardButtonColor.SECONDARY
            )
            buttons += 1
        else:
            keyboard.add(
                Callback(
                    obj,
                    {
                        'user_id': event.user_id, 'type': payload['type'][:-1],
                        'filter': payload['filter'], 'page': page, 'obj': obj, 'obj_data': 'information'
                    }
                ),
                KeyboardButtonColor.SECONDARY
            )
            keyboard.row()
            keyboard.add(
                Callback('К выбору раздела', {'user_id': event.user_id, 'type': f"{payload['type']}_type", 'page': 0}),
                KeyboardButtonColor.POSITIVE
            )
            keyboard.row()
            if page != 0:
                keyboard.add(
                    Callback(
                        'Назад',
                        {
                            'user_id': event.user_id, 'type': payload['type'],
                            'filter': payload['filter'], 'page': page - 1
                        }
                    ),
                    KeyboardButtonColor.PRIMARY
                )
            keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
            if len(objects)-(i + 1) > 0:
                keyboard.add(
                    Callback(
                        'Далее',
                        {
                            'user_id': event.user_id, 'type': payload['type'],
                            'filter': payload['filter'], 'page': page + 1
                        }
                    )
                )
                page += 1
            buttons = 0
            keyboards.append(keyboard.get_json())
            keyboard = Keyboard(one_time=False, inline=True)

    if not keyboards:
        keyboard.add(
            Callback('К выбору раздела', {'user_id': event.user_id, 'type': f"{payload['type']}_type", 'page': 0}),
            KeyboardButtonColor.POSITIVE
        )
        keyboard.row()
        keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
        keyboards.append(keyboard.get_json())

    await event.edit_message(f"Поиск по разделу '{payload['filter']}'!", keyboard=keyboards[payload['page']])


def _get_object_payload(user_id: int, payload, obj_data: str) -> dict[str, str | int]:
    payload = {
        'user_id': user_id,
        'type': payload['type'],
        'filter': payload['filter'],
        'page': payload['page'],
        'obj': payload['obj'],
        'obj_data': obj_data
    }
    return payload


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['character']))
async def get_character(event: MessageEvent, payload: Payload) -> None:
    character = CharacterParser()
    data_types = {
        'information': ('Основная информация', character.get_information),
        'active_skills': ('Активные навыки', character.get_active_skills),
        'passive_skills': ('Пассивные навыки', character.get_passive_skills),
        'constellations': ('Созвездия', character.get_constellations),
        'ascension': ('Возвышение', upload)
    }
    keyboard = Keyboard(one_time=False, inline=True)

    for data in data_types:
        if data != payload['obj_data']:
            keyboard.add(
                Callback(data_types[data][0], _get_object_payload(event.user_id, payload, data)),
                KeyboardButtonColor.SECONDARY
            )
            keyboard.row()

    keyboard.add(
        Callback(
            'К списку персонажей',
            {'user_id': event.user_id, 'type': 'characters', 'filter': payload['filter'], 'page': payload['page']}
        ),
        KeyboardButtonColor.POSITIVE
    )
    keyboard.row()
    keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    name_en = json.load('characters')[payload['filter']][payload['obj']].split('/')[-2]
    if payload['obj_data'] != 'ascension':
        url = f"{character.base_url}img/char/{name_en}.png"
        attachment = await character.get_icon_attachment(bp.api, url)
        message = await data_types[payload['obj_data']][1](payload['obj'], payload['filter'])
    else:
        attachment = await get_attachment_icon(f"{ASCENSION}{os.sep}{name_en}.png")
        message = f"🖼Материалы возвышения персонажа '{payload['obj']}':"

    await event.edit_message(message, attachment=attachment, keyboard=keyboard.get_json())


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['weapon']))
async def get_weapon(event: MessageEvent, payload: Payload) -> None:
    weapon = WeaponParser()
    data_types = {
        'information': ('Основная информация', weapon.get_information),
        'ability': ('Способность оружия', weapon.get_ability),
        'progression': ('Прогрессия', weapon.get_progression),
        'refinement': ('Пробуждение', weapon.get_refinement),
        'story': ('История', weapon.get_story)
    }
    keyboard = Keyboard(one_time=False, inline=True)

    for data in data_types:
        if data != payload['obj_data']:
            keyboard.add(
                Callback(data_types[data][0], _get_object_payload(event.user_id, payload, data)),
                KeyboardButtonColor.SECONDARY
            )
            keyboard.row()

    keyboard.add(
        Callback(
            'К списку оружия',
            {'user_id': event.user_id, 'type': 'weapons', 'filter': payload['filter'], 'page': payload['page']}
        ),
        KeyboardButtonColor.POSITIVE
    )
    keyboard.row()
    keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    code = json.load('weapons')[payload['filter']][payload['obj']][0]
    await event.edit_message(
        await data_types[payload['obj_data']][1](payload['obj'], payload['filter']),
        attachment=await weapon.get_icon_attachment(bp.api, f"{weapon.base_url}img/weapon/{code}.png"),
        keyboard=keyboard.get_json()
    )


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['artifact']))
async def get_artifact(event: MessageEvent, payload: Payload) -> None:
    artifact = ArtifactParser()
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(
            Callback(
                'К списку артефактов',
                {'user_id': event.user_id, 'type': 'artifacts', 'filter': payload['filter'], 'page': payload['page']}
            ),
            KeyboardButtonColor.POSITIVE
        )
        .row()
        .add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    icon = json.load('artifacts')[payload['filter']][payload['obj']][-1]
    await event.edit_message(
        await artifact.get_information(payload['obj'], payload['filter']),
        attachment=await artifact.get_icon_attachment(bp.api, icon),
        keyboard=keyboard.get_json()
    )


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['enemie']))
async def get_enemy(event: MessageEvent, payload: Payload) -> None:
    enemy = EnemyParser()
    data_types = {
        'information': ('Основная информация', enemy.get_information),
        'progression': ('Прогрессия', enemy.get_progression)
    }
    keyboard = Keyboard(one_time=False, inline=True)

    for data in data_types:
        if data != payload['obj_data']:
            keyboard.add(
                Callback(data_types[data][0], _get_object_payload(event.user_id, payload, data)),
                KeyboardButtonColor.SECONDARY
            )
            keyboard.row()

    keyboard.add(
        Callback(
            'К списку противников',
            {'user_id': event.user_id, 'type': 'enemies', 'filter': payload['filter'], 'page': payload['page']}
        ),
        KeyboardButtonColor.POSITIVE
    )
    keyboard.row()
    keyboard.add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)

    code = json.load('enemies')[payload['filter']][payload['obj']]
    await event.edit_message(
        await data_types[payload['obj_data']][1](payload['obj'], payload['filter']),
        attachment=await enemy.get_icon_attachment(bp.api, f"{enemy.base_url}img/enemy/{code}.png"),
        keyboard=keyboard.get_json()
    )


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['book']))
async def get_book(event: MessageEvent, payload: Payload) -> None:
    book = BookParser()
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(
            Callback(
                'К томам книги',
                {'user_id': event.user_id, 'type': 'books', 'filter': payload['filter'], 'page': payload['page']}
            ),
            KeyboardButtonColor.POSITIVE
        )
        .row()
        .add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    icon = await book.get_icon_attachment(bp.api, json.load('books')[payload['filter']][payload['obj']][-1])
    message, doc = await book.get_information(event.peer_id, bp.api, payload['filter'], payload['obj'])
    await event.edit_message(
        message,
        attachment=f"{icon},{doc}",
        keyboard=keyboard.get_json()
    )


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(['domain']))
async def get_domain(event: MessageEvent, payload: Payload) -> None:
    domain = DomainParser()
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(
            Callback(
                'К списку подземелий',
                {'user_id': event.user_id, 'type': 'domains', 'filter': payload['filter'], 'page': payload['page']}
            ),
            KeyboardButtonColor.POSITIVE
        )
        .row()
        .add(Callback('Меню', {'user_id': event.user_id, 'type': 'menu'}), KeyboardButtonColor.POSITIVE)
    )

    message = await domain.get_information(payload['obj'], payload['filter'])
    attachment = await get_attachment_icon(
        await get_domain_image(
            json.load('domains')[payload['filter']][payload['obj']][-1],
            await domain.get_monsters(payload['obj'], payload['filter']),
            await domain.get_drop(payload['obj'], payload['filter'])
        )
    )
    await event.edit_message(message, attachment=attachment, keyboard=keyboard.get_json())
