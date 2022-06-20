import os
import re
from typing import Optional

from vkbottle import Keyboard, KeyboardButtonColor, Callback, GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent
from vkbottle_types.objects import MessagesKeyboard

from bot.parsers import CharacterParser, WeaponParser, ArtifactParser, EnemyParser, BookParser
from bot.rules import CommandRule, EventRule
from bot.utils import PostgresConnection, json
from bot.errors import IncompatibleOptions
from bot.utils.files import upload
from bot.validators.genshindb import GenshinDBValidator
from bot.src.manuals import genshindb as man
from bot.config.dependencies.paths import DATABASE_APPEARANCE, ASCENSION


bp = Blueprint('GenshinDatabase')


def _get_menu_keyboard(user_id: int) -> str:
    keyboard = (
        Keyboard(one_time=False, inline=True)
        .add(
            Callback('Персонажи', {'user_id': user_id, 'type': 'characters_type', 'page': 0}),
            KeyboardButtonColor.PRIMARY
        )
        .row()
        .add(
            Callback('Оружие', {'user_id': user_id, 'type': 'weapons_type', 'page': 0}),
            KeyboardButtonColor.PRIMARY
        )
        .row()
        .add(
            Callback('Артефакты', {'user_id': user_id, 'type': 'artifacts_type', 'page': 0}),
            KeyboardButtonColor.PRIMARY
        )
        .row()
        .add(
            Callback('Противники', {'user_id': user_id, 'type': 'enemies_type', 'page': 0}),
            KeyboardButtonColor.PRIMARY
        )
        .row()
        .add(
            Callback('Книги', {'user_id': user_id, 'type': 'books_type', 'page': 0}),
            KeyboardButtonColor.PRIMARY
        )
    )
    return keyboard.get_json()


async def _parse_shortcut(message: Message) -> tuple[Optional[MessagesKeyboard], str, str]:
    reply_message = (
        await message.ctx_api.messages.get_by_conversation_message_id(
            message.peer_id, [message.reply_message.conversation_message_id]
        )
    ).items[0]
    keyboard = reply_message.keyboard
    delattr(keyboard, 'author_id')
    msg = reply_message.text.replace("'", '"')
    photo = reply_message.attachments[0].photo if reply_message.attachments else None
    photo_id = f"photo{photo.owner_id}_{photo.id}" if photo else ''
    return keyboard, msg, photo_id


async def _get_certain_shortcut(user_id: int, shortcut: str) -> dict[str, str | int]:
    async with PostgresConnection() as connection:
        shortcut = await connection.fetchrow(f"""
            SELECT message, photo_id, keyboard FROM genshin_db_shortcuts 
            WHERE user_id = {user_id} AND shortcut = '{shortcut}';
        """)
        return dict(shortcut)


async def _get_shortcuts(user_id: int) -> str:
    async with PostgresConnection() as connection:
        shortcuts = await connection.fetch(
            f"SELECT shortcut FROM genshin_db_shortcuts WHERE user_id = {user_id};"
        )
        return '\n'.join([dict(s)['shortcut'] for s in shortcuts])


async def _create_shortcut(user_id: int, name: str, message: str, photo_id: str, keyboard: str) -> None:
    async with PostgresConnection() as connection:
        await connection.execute(f"""
            INSERT INTO genshin_db_shortcuts VALUES (
                {user_id}, '{name}', '{message}', '{photo_id}', '{keyboard}'
            );
        """)


async def _remove_shortcut(user_id: int, name: str) -> None:
    async with PostgresConnection() as connection:
        await connection.execute(f"""
            DELETE FROM genshin_db_shortcuts WHERE shortcut = '{name}' AND user_id = {user_id};
        """)


def _change_keyboard_owner(keyboard: MessagesKeyboard, user_id: int) -> MessagesKeyboard:
    for b in keyboard.buttons:
        b[0]['action']['payload'] = re.sub(r'"user_id":\d+', f'"user_id":{user_id}', b[0]['action']['payload'])
    return keyboard


@bp.on.message(CommandRule(('гдб',), options=('-п', '-аш', '-дш', '-ш')))
async def get_genshin_database(message: Message, options: tuple[str, ...]) -> None:
    async with GenshinDBValidator(message) as validator:
        match options:
            case ('-[error]',) | ('-п',):
                await message.answer(man.GenshinDatabase.options[options[0]])
            case ('-[default]',):
                shortcut = re.sub(r'^!гдб\s|\{|}', '', message.text)
                if not shortcut:
                    await message.answer(
                        message=f"Доброго времени суток, {(await message.get_user()).first_name}!",
                        attachment=await upload(bp.api, 'photo_messages', DATABASE_APPEARANCE + os.sep + 'menu.png'),
                        keyboard=_get_menu_keyboard(message.from_id)
                    )
                    return None
                await validator.check_shortcut_exist(shortcut, message.from_id)
                shortcut = await _get_certain_shortcut(message.from_id, shortcut)
                await message.answer(
                    message=shortcut['message'],
                    attachment=shortcut['photo_id'] if shortcut['photo_id'] else None,
                    keyboard=shortcut['keyboard']
                )
            case ('-аш',):
                shortcut = re.sub(r'^\s+|\{|}', '', message.text[message.text.find('-аш') + 3:])
                validator.check_shortcut_specified(shortcut)
                await validator.check_shortcut_new(shortcut, message.from_id)
                validator.check_reply_message(message.reply_message)
                keyboard, msg, photo_id = await _parse_shortcut(message)
                validator.check_reply_message_keyboard(keyboard)
                keyboard = _change_keyboard_owner(keyboard, message.from_id)
                await _create_shortcut(message.from_id, shortcut, msg, photo_id, keyboard.json())
                await message.answer(f"Шорткат '{shortcut}' был успешно создан!")
            case ('-дш',):
                shortcut = re.sub(r'^\s+|\{|}', '', message.text[message.text.find('-дш') + 3:])
                validator.check_shortcut_specified(shortcut)
                await validator.check_shortcut_exist(shortcut, message.from_id)
                await _remove_shortcut(message.from_id, shortcut)
                await message.answer(f"Шорткат '{shortcut}' был успешно удален!")
            case ('-ш',):
                await validator.check_shortcuts_created(message.from_id)
                await message.answer('Список ваших шорткатов:\n' + await _get_shortcuts(message.from_id))
            case _:
                raise IncompatibleOptions(options)


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('menu',)))
async def return_to_menu(event: MessageEvent, payload: dict[str, str | int]) -> None:
    await event.edit_message(
        f"Доброго времени суток, {(await event.ctx_api.users.get([payload['user_id']]))[0].first_name}!",
        attachment=await upload(bp.api, 'photo_messages', DATABASE_APPEARANCE + os.sep + 'menu.png'),
        keyboard=_get_menu_keyboard(payload['user_id'])
    )


async def _get_attachment_icon(icon_path: str) -> Optional[str]:
    """
    Check if icon exists.
    If yes, then upload it to vk server and return formatted attachments string.
    """
    if not os.path.exists(icon_path):
        return None
    return await upload(bp.api, 'photo_messages', icon_path)


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    EventRule(('characters_type', 'weapons_type', 'artifacts_type', 'enemies_type', 'books_type'))
)
async def get_type_filters(event: MessageEvent, payload: dict[str, str | int]) -> None:
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
        attachment=await _get_attachment_icon(f"{DATABASE_APPEARANCE}{os.sep}{payload_type}.png")
    )


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('characters', 'weapons', 'artifacts', 'enemies', 'books'))
)
async def get_filtered_objects(event: MessageEvent, payload: dict[str, str | int]) -> None:
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


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('character',)))
async def get_character(event: MessageEvent, payload: dict[str, str | int]) -> None:
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
        attachment = await _get_attachment_icon(f"{ASCENSION}{os.sep}{name_en}.png")
        message = f"🖼Материалы возвышения персонажа '{payload['obj']}':"

    await event.edit_message(message, attachment=attachment, keyboard=keyboard.get_json())


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('weapon',)))
async def get_weapon(event: MessageEvent, payload: dict[str, str | int]) -> None:
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


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('artifact',)))
async def get_artifact(event: MessageEvent, payload: dict[str, str | int]) -> None:
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


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('enemie',)))
async def get_enemy(event: MessageEvent, payload: dict[str, str | int]) -> None:
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


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('book',)))
async def get_book(event: MessageEvent, payload: dict[str, str | int]) -> None:
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
