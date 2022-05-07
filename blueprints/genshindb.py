import os
from typing import Tuple, Dict, List

from vkbottle import Keyboard, KeyboardButtonColor, Callback, GroupEventType
from vkbottle.bot import Blueprint, Message, MessageEvent

from bot.parsers import CharacterParser, WeaponParser, ArtifactParser, EnemyParser, BookParser
from bot.rules import CommandRule, EventRule
from bot.utils import PostgresConnection, json
from bot.utils.files import upload
from bot.src.types.help import genshindb as hints
from bot.config.dependencies.paths import DATABASE_APPEARANCE, ASCENSION


bp = Blueprint('GenshinDatabase')


async def _get_username(user_id: int) -> str:
    async with PostgresConnection() as connection:
        username = await connection.fetchrow(f"SELECT first_name FROM users WHERE user_id = {user_id};")
        return dict(username)['first_name']


def _get_keyboard_menu(user_id: int) -> str:
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


@bp.on.message(CommandRule(('гдб',), options=('-[default]', '-[error]', '-п')))
async def get_started(message: Message, options: Tuple[str, ...] = ('-[default]',)) -> None:
    if options[0] in hints.GenshinDatabase.slots.value:
        await message.answer(hints.GenshinDatabase.slots.value[options[0]])
        return None

    await message.answer(
        f"Доброго времени суток, {await _get_username(message.from_id)}!",
        attachment=await upload(bp.api, 'photo_messages', DATABASE_APPEARANCE + os.sep + 'menu.png'),
        keyboard=_get_keyboard_menu(message.from_id)
    )


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('menu',)))
async def return_to_menu(event: MessageEvent, payload: Dict[str, str | int]) -> None:
    await event.edit_message(
        f"Доброго времени суток, {await _get_username(payload['user_id'])}!",
        attachment=await upload(bp.api, 'photo_messages', DATABASE_APPEARANCE + os.sep + 'menu.png'),
        keyboard=_get_keyboard_menu(payload['user_id'])
    )


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    EventRule(('characters_type', 'weapons_type', 'artifacts_type', 'enemies_type', 'books_type'))
)
async def get_type_filters(event: MessageEvent, payload: Dict[str, str | int]) -> None:
    payload_type = payload['type'].split('_')[0]
    page = 0
    buttons = 0
    filters = json.load(payload_type)

    keyboards: List[str] = []
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

    if os.path.exists(f"{DATABASE_APPEARANCE}{os.sep}{payload_type}.png"):
        attachment = await upload(bp.api, 'photo_messages', f"{DATABASE_APPEARANCE}{os.sep}{payload_type}.png")
    else:
        attachment = None
    await event.edit_message(
        'Пожалуйста, выберите интересующий вас раздел!',
        keyboard=keyboards[payload['page']],
        attachment=attachment
    )


@bp.on.raw_event(
    GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('characters', 'weapons', 'artifacts', 'enemies', 'books'))
)
async def get_filtered_objects(event: MessageEvent, payload: Dict[str, str | int]) -> None:
    page = 0
    buttons = 0
    objects = json.load(payload['type'])[payload['filter']]

    keyboards: List[str] = []
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


def _get_object_payload(user_id: int, payload, obj_data: str) -> Dict[str, str | int]:
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
async def get_character(event: MessageEvent, payload: Dict[str, str | int]) -> None:
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
        if os.path.exists(f"{ASCENSION}{os.sep}{name_en}.png"):
            attachment = await data_types[payload['obj_data']][1](
                bp.api, 'photo_messages', f"{ASCENSION}{os.sep}{name_en}.png"
            )
        else:
            attachment = None
        message = f"🖼Материалы возвышения персонажа '{payload['obj']}':"
    await event.edit_message(message, attachment=attachment, keyboard=keyboard.get_json())


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, EventRule(('weapon',)))
async def get_weapon(event: MessageEvent, payload: Dict[str, str | int]) -> None:
    weapon = WeaponParser()
    data_types = {
        'information': ('Основная информация', weapon.get_information),
        'ability': ('Способность оружия', weapon.get_ability),
        'progression': ('Прогрессия', weapon.get_progression),
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
async def get_artifact(event: MessageEvent, payload: Dict[str, str | int]) -> None:
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
async def get_enemy(event: MessageEvent, payload: Dict[str, str | int]) -> None:
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
async def get_book(event: MessageEvent, payload: Dict[str, str | int]) -> None:
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
