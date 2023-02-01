import os
import re
from typing import Optional

from vkbottle import Keyboard, KeyboardButtonColor, Callback
from vkbottle.bot import BotLabeler, Message, MessageEvent
from vkbottle_types.objects import MessagesKeyboard, GroupsGroupFull

from bot.src import Options, Payload
from bot.src.config import bot
from bot.src.config.dependencies.group import SHORTNAME
from bot.src.parsers.honeyimpact import *
from bot.src.rules import CommandRule, EventRule
from bot.src.utils import PostgresConnection, json
from bot.src.utils.files import download, upload
from bot.src.errors import IncompatibleOptions
from bot.src.validators.genshindb import GenshinDBValidator
from bot.src.manuals import genshindb as man
from bot.src.imageprocessing.genshin.genshindb import *
from bot.src.templates import honeyimpact as tpl


bl = BotLabeler()


class GenshinDB:
    CATEGORIES = {
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

    async def add_shortcut(self) -> str:
        shortcut = self.message.text[self.message.text.find('~~аш') + 4:].strip()
        self.validator.check_shortcut_specified(shortcut)
        await self.validator.check_shortcut_new(shortcut, self.message.from_id)
        self.validator.check_reply_message(self.message.reply_message)
        keyboard, msg, photo_id = await self._parse_shortcut_data()
        self.validator.check_reply_message_keyboard(keyboard)
        self.validator.check_keyboard_handler(keyboard, self.__class__.__name__)
        keyboard = self._change_keyboard_owner(keyboard)
        await self._add_shortcut_to_db(shortcut, msg, photo_id, keyboard)
        return shortcut

    async def delete_shortcut(self) -> str:
        shortcut = self.message.text[self.message.text.find('~~дш') + 4:].strip()
        self.validator.check_shortcut_specified(shortcut)
        await self.validator.check_shortcut_exist(shortcut, self.message.from_id)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                DELETE FROM genshindb_shortcuts WHERE shortcut = $1 AND user_id = {self.message.from_id};
            """, shortcut)
        return shortcut

    async def get_user_shortcuts(self) -> str:
        await self.validator.check_shortcuts_created(self.message.from_id)
        async with PostgresConnection() as connection:
            shortcuts = await connection.fetch(
                f"SELECT shortcut FROM genshindb_shortcuts WHERE user_id = {self.message.from_id};"
            )
            return 'Список ваших шорткатов:\n' + '\n'.join(dict(s)['shortcut'] for s in shortcuts)

    @staticmethod
    async def get_main_menu(user_id: int, group: GroupsGroupFull) -> dict[str, str, str]:
        message = f"Доброго времени суток, {(await bot.group.api.users.get([user_id]))[0].first_name}!"
        menu_path = await MenuImageGenerator(list(GenshinDB.CATEGORIES.values()), group).generate()
        attachment = await upload(bot.group.api, 'photo_messages', menu_path)
        os.remove(menu_path)
        keyboard = GenshinDB._get_interactive_keyboard(user_id)
        return {'message': message, 'attachment': attachment, 'keyboard': keyboard}

    async def get(self) -> None:
        shortcut = re.sub(r'^!гдб\s?', '', self.message.text)
        if not shortcut:
            group = (await self.message.ctx_api.groups.get_by_id([SHORTNAME], fields=['photo_200']))[0]
            await self.message.answer(**(await self.get_main_menu(self.message.from_id, group)))
            return None
        await self.validator.check_shortcut_exist(shortcut, self.message.from_id)
        shortcut = await self._fetch_shortcut_from_db(shortcut)
        await self.message.answer(
            message=shortcut['message'],
            attachment=shortcut['photo_id'] if shortcut['photo_id'] else None,
            keyboard=shortcut['keyboard']
        )

    @staticmethod
    async def fetch_page(name: str, page: int, token: list[str] | str) -> Optional[str]:
        """Fetch page from genshindb_pages.

        :param name: Category/section name
        :param page: Page number
        :param token: Special token
        :return: Page attachment string or None
        """
        token = GenshinDB._process_token(token)
        async with PostgresConnection() as connection:
            attachment = await connection.fetchrow(
                f"SELECT photo_id FROM genshindb_pages WHERE name = '{name}' AND page = {page} AND token = '{token}';"
            )
            if attachment is not None:
                attachment = dict(attachment)['photo_id']
            return attachment or await GenshinDB._delete_page(name, page)

    @staticmethod
    async def push_page(name: str, page: int, photo_id: str, token: list[str] | str) -> None:
        """Push page to genshindb_pages.

        :param name: Category/section name
        :param page: Page number
        :param photo_id: Page attachment string
        :param token: Special token
        :return: None
        """
        photo_id = photo_id.rsplit('_', maxsplit=1)[0]
        token = GenshinDB._process_token(token)
        async with PostgresConnection() as connection:
            await connection.execute(f"""
                INSERT INTO genshindb_pages VALUES ('{name}', {page}, '{photo_id}', '{token}');
            """)

    @staticmethod
    def _get_interactive_keyboard(user_id: int) -> str:
        kb = Keyboard(inline=True)
        for i, values in enumerate(GenshinDB.CATEGORIES.items()):
            button_type, label = values
            kb.add(
                Callback(label, {'handler': GenshinDB.__name__, 'user_id': user_id, 'type': button_type, 'cat': label}),
                KeyboardButtonColor.PRIMARY
            )
            if (i + 1) % 2 == 0:
                kb.row()
        kb.add(
            Callback('Выйти', {'handler': GenshinDB.__name__, 'user_id': user_id, 'type': 'exit'}),
            KeyboardButtonColor.NEGATIVE
        )
        return kb.get_json()

    async def _parse_shortcut_data(self) -> tuple[MessagesKeyboard, str, str]:
        reply_msg = (
            await self.message.ctx_api.messages.get_by_conversation_message_id(
                self.message.peer_id, [self.message.reply_message.conversation_message_id]
            )
        ).items[0]
        keyboard = reply_msg.keyboard
        if keyboard is not None:
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
                INSERT INTO genshindb_shortcuts VALUES (
                    {self.message.from_id}, $1, $2, '{photo_id}', '{keyboard.json()}'
                );
            """, shortcut, msg)

    async def _fetch_shortcut_from_db(self, shortcut: str) -> dict[str, str | int]:
        async with PostgresConnection() as connection:
            shortcut = await connection.fetchrow(f"""
                SELECT message, photo_id, keyboard FROM genshindb_shortcuts 
                WHERE user_id = {self.message.from_id} AND shortcut = $1;
            """, shortcut)
            return dict(shortcut)

    @staticmethod
    async def _delete_page(name: str, page: int) -> None:
        """Delete page with outdated token from genshindb_pages.

        :param name: Category/section name
        :param page: Page number
        :return: None
        """
        async with PostgresConnection() as connection:
            await connection.execute(f"DELETE FROM genshindb_pages WHERE name = '{name}' AND page = {page};")

    @staticmethod
    def _process_token(token: list[str] | str) -> str:
        return '/'.join(token) if isinstance(token, list) else token


@bl.message(CommandRule(['гдб'], ['~~п', '~~аш', '~~дш', '~~ш'], man.GenshinDB))
async def get_genshin_database(message: Message, options: Options) -> None:
    async with GenshinDBValidator(message) as validator:
        genshin_db = GenshinDB(message, validator)
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


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['menu']))
async def return_to_menu(event: MessageEvent, payload: Payload) -> None:
    group = (await event.ctx_api.groups.get_by_id([SHORTNAME], fields=['photo_200']))[0]
    await event.edit_message(**(await GenshinDB.get_main_menu(payload['user_id'], group)))


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['exit']))
async def exit_from_db(event: MessageEvent, **_) -> None:
    await event.edit_message('Произведен выход из интерактивной базы данных.', keyboard=Keyboard().get_json())


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, list(GenshinDB.CATEGORIES)))
async def get_db_sections(event: MessageEvent, payload: Payload) -> None:
    keyboards = []
    kb = Keyboard(inline=True)
    pl_type = payload['type'].split('_')[0]
    sections = json.load(pl_type)
    apl = payload.copy()  #: additional payload
    apl['type'] = pl_type

    tokens = [[]]
    section_names = [[]]
    buttons = 0
    last = list(sections)[-1]
    for section, objects in sections.items():
        page = len(keyboards)
        if payload['cat'] == 'Персонажи':
            section_name = os.path.join(section)
        else:
            section_name = await download(objects[list(objects.keys())[-1]][1], force=False)  #: last object in section
        tokens[page].append(section)
        section_names[page].append(section_name)
        apl['sect'] = section
        apl['s_page'] = page
        kb.add(Callback(section, apl.copy()))
        buttons += 1
        if buttons % 2 == 0 and section != last:
            kb.row()
        elif buttons % 7 == 0 or section == last:
            epl = payload.copy()  #: extra payload for page control buttons
            kb.row()
            if page != 0:
                epl['s_page'] = page - 1
                kb.add(Callback('Назад', epl.copy()), KeyboardButtonColor.PRIMARY)
            kb.add(
                Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
                KeyboardButtonColor.POSITIVE
            )
            if section != last:
                epl['s_page'] = page + 1
                kb.add(Callback('Далее', epl.copy()), KeyboardButtonColor.PRIMARY)
                tokens.append([])
                section_names.append([])
            keyboards.append(kb.get_json())
            kb = Keyboard(inline=True)
            buttons = 0

    page = payload.get('s_page', 0)
    fetched_page = await GenshinDB.fetch_page(payload['cat'], page, tokens[page])
    if fetched_page is not None:
        attachment = fetched_page
    else:
        section_path = await SectionImageGenerator(section_names[page], page + 1, payload['cat']).generate()
        attachment = await upload(bot.group.api, 'photo_messages', section_path)
        os.remove(section_path)
        await GenshinDB.push_page(payload['cat'], page, attachment, tokens[page])
    await event.edit_message(f"Просмотр категории '{payload['cat']}'!", attachment=attachment, keyboard=keyboards[page])


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, [c.split('_')[0] for c in GenshinDB.CATEGORIES]))
async def get_section_objects(event: MessageEvent, payload: Payload) -> None:
    keyboards = []
    kb = Keyboard(inline=True)
    objects = json.load(payload['type'])[payload['sect']]
    apl = payload.copy()  #: additional payload
    apl['type'] = payload['type'][:-1]

    tokens = [[]]
    object_urls = [[]]
    buttons = 0
    last = list(objects)[-1]
    for obj, data in objects.items():
        page = len(keyboards)
        tokens[page].append(obj)
        object_urls[page].append(data[1])  #: object icon url
        apl['obj'] = obj
        apl['o_page'] = page
        kb.add(Callback(obj, apl.copy()))
        buttons += 1
        if buttons % 2 == 0 and buttons % 6 != 0 and obj != last:
            kb.row()
        elif buttons % 6 == 0 or obj == last:
            epl = payload.copy()  #: extra payload for page control buttons
            epl['type'] = f"{payload['type']}_type"
            del epl['sect']
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
                Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
                KeyboardButtonColor.POSITIVE
            )
            if obj != last:
                epl['o_page'] = page + 1
                kb.add(Callback('Далее', epl.copy()), KeyboardButtonColor.PRIMARY)
                tokens.append([])
                object_urls.append([])
            keyboards.append(kb.get_json())
            kb = Keyboard(inline=True)
            buttons = 0

    page = payload.get('o_page', 0)
    fetched_page = await GenshinDB.fetch_page(payload['sect'], page, tokens[page])
    if fetched_page is not None:
        attachment = fetched_page
    else:
        object_path = await ObjectImageGenerator(object_urls[page], page + 1, payload['sect']).generate()
        attachment = await upload(bot.group.api, 'photo_messages', object_path)
        os.remove(object_path)
        await GenshinDB.push_page(payload['sect'], page, attachment, tokens[page])
    await event.edit_message(f"Просмотр раздела '{payload['sect']}'!", attachment=attachment, keyboard=keyboards[page])


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['character']))
async def get_character(event: MessageEvent, payload: Payload) -> None:
    character = CharacterParser(payload['sect'], payload['obj'])
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
    del apl['obj']
    del apl['data']
    kb.add(Callback('К списку персонажей', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(
        Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
        KeyboardButtonColor.POSITIVE
    )

    if payload.get('data', default) != 'ascension':
        attachment = await upload(bot.group.api, 'photo_messages', await download(character.icon, force=False))
        message = await buttons[payload.get('data', default)][1]()
    else:
        ascension_path = await AscensionImageGenerator(character.name, await character.get_ascension()).generate()
        attachment = await upload(bot.group.api, 'photo_messages', ascension_path)
        os.remove(ascension_path)
        message = f"🖼Материалы возвышения персонажа '{character.name}':"

    await event.edit_message(message, attachment=attachment, keyboard=kb.get_json())


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['weapon']))
async def get_weapon(event: MessageEvent, payload: Payload) -> None:
    weapon = WeaponParser(payload['sect'], payload['obj'])
    buttons = {
        'information': 'Основная информация',
        'ability': 'Способность оружия',
        'progression': 'Прогрессия',
        'refinement': 'Пробуждение',
        'story': 'История'
    }
    kb = Keyboard(inline=True)
    apl = payload.copy()

    default = list(buttons)[0]
    for data, label in buttons.items():
        if data != payload.get('data', default):
            apl['data'] = data
            kb.add(Callback(label, apl.copy()))
            kb.row()
    apl['type'] = f"{payload['type']}s"
    del apl['obj']
    del apl['data']
    kb.add(Callback('К списку оружия', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(
        Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
        KeyboardButtonColor.POSITIVE
    )

    message = None
    attachment = None
    match payload.get('data'):
        case 'information':
            message = await weapon.get_information()
        case 'ability':
            message = await weapon.get_ability()
        case 'progression':
            image = await WeaponProgressionImageGenerator(weapon.icon, await weapon.get_progression()).generate()
            attachment = await upload(
                bot.group.api,
                'photo_messages',
                image
            )
            os.remove(image)
        case 'refinement':
            message = await weapon.get_refinement()
        case _:
            message = await weapon.get_information()
    attachment = attachment or await upload(bot.group.api, 'photo_messages', await download(weapon.icon, force=False))
    await event.edit_message(message, attachment=attachment, keyboard=kb.get_json())


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['artifact']))
async def get_artifact(event: MessageEvent, payload: Payload) -> None:
    artifact = ArtifactParser(payload['sect'], payload['obj'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['obj']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К списку артефактов', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(
            Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
            KeyboardButtonColor.POSITIVE
        )
    )

    await event.edit_message(
        await artifact.get_information(),
        attachment=await upload(bot.group.api, 'photo_messages', await download(artifact.icon, force=False)),
        keyboard=kb.get_json()
    )


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['enemie']))
async def get_enemy(event: MessageEvent, payload: Payload) -> None:
    enemy = EnemyParser(payload['sect'], payload['obj'])
    buttons = {
        'information': 'Основная информация',
        'progression': 'Прогрессия'
    }
    kb = Keyboard(inline=True)
    apl = payload.copy()

    default = list(buttons)[0]
    for data, label in buttons.items():
        if data != payload.get('data', default):
            apl['data'] = data
            kb.add(Callback(label, apl.copy()))
            kb.row()
    apl['type'] = f"{payload['type']}s"
    del apl['obj']
    del apl['data']
    kb.add(Callback('К списку противников', apl.copy()), KeyboardButtonColor.POSITIVE)
    kb.row()
    kb.add(
        Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
        KeyboardButtonColor.POSITIVE
    )

    message = None
    match payload.get('data'):
        case 'progression':
            image = await EnemyProgressionImageGenerator(enemy.icon, await enemy.get_progression()).generate()
            attachment = await upload(
                bot.group.api,
                'photo_messages',
                image
            )
            os.remove(image)
        case _:
            information = await enemy.get_information()
            message = tpl.enemies.format_information(information)
            image = await EnemyDropImageGenerator(enemy.icon, information.drop).generate()
            attachment = await upload(
                bot.group.api,
                'photo_messages',
                image
            )
            os.remove(image)
    await event.edit_message(message, attachment=attachment, keyboard=kb.get_json())


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['book']))
async def get_book(event: MessageEvent, payload: Payload) -> None:
    book = BookParser(payload['sect'], payload['obj'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['obj']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К оглавлению', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(
            Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
            KeyboardButtonColor.POSITIVE
        )
    )

    icon = await upload(bot.group.api, 'photo_messages', await download(book.icon, force=False))
    message = await book.get_information()
    book = await book.save()
    book_path, book_name = book, book.rsplit(os.sep, maxsplit=1)[1]
    doc = await upload(bot.group.api, 'document_messages', book_name, book_path, peer_id=event.peer_id)
    os.remove(book_path)
    await event.edit_message(
        message,
        attachment=f"{icon},{doc}",
        keyboard=kb.get_json()
    )


@bl.raw_event('message_event', MessageEvent, EventRule(GenshinDB, ['domain']))
async def get_domain(event: MessageEvent, payload: Payload) -> None:
    domain = DomainParser(payload['sect'], payload['obj'])
    apl = payload.copy()
    apl['type'] = f"{payload['type']}s"
    del apl['obj']
    kb = (
        Keyboard(inline=True)
        .add(Callback('К списку подземелий', apl.copy()), KeyboardButtonColor.POSITIVE)
        .row()
        .add(
            Callback('Меню', {'handler': GenshinDB.__name__, 'user_id': payload['user_id'], 'type': 'menu'}),
            KeyboardButtonColor.POSITIVE
        )
    )

    image_path = await DomainImageGenerator(domain.icon, domain.monsters, domain.rewards).generate()
    attachment = await upload(bot.group.api, 'photo_messages', image_path)
    os.remove(image_path)
    await event.edit_message(
        await domain.get_information(),
        attachment=attachment,
        keyboard=kb.get_json()
    )
