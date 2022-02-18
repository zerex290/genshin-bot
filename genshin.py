import pickle
import datetime
from time import sleep
import traceback

import genshinstats as gs

import constants
import templates.genshin
from wrappers import genshinwrap
import honeyimpact


class Main:
    """Отсюда можно команды сделать в одной!!!"""

    @staticmethod
    @genshinwrap.get_ps_pictures
    def get_daily_farm(api, chat_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=farm
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с изображением тех персонажей и \
        оружия, ресурсы для возвышения которых доступны на сегодняшний день.
        \n Синтаксис: !фарм [опции]\
        \n -п >>> текущая справка по команде\
        """
        # сделать так, чтобы можно было показывать фарм ресы на любой день через опции (-пн, -вт, -ср и т.п.)

        file_directory = f"/home/Moldus/vkbot/genshin/daily_farm/{datetime.datetime.now().weekday()}.png"
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'data': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    @genshinwrap.get_ascension_materials
    def get_ascension_materials(api, chat_id: int, character: str) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=farm
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с изображением материалов \
        возвышения определенного персонажа.
        \n Синтаксис: !ресы [опции] [имя персонажа]\
        \n -п >>> текущая справка по команде\
        """

        if not character:
            return {'error': 'Вы не указали имя персонажа!'}
        file_directory = constants.Genshin.ASCENSION.get(character.replace(' ', ''), None)
        if not file_directory:
            return {'error': f"Ошибка в имени персонажа {character}!"}
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'data': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    @genshinwrap.get_ps_pictures
    def get_boss_materials(api, chat_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=talanty
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с изображением материалов \
        боссов, используемых определенными персонажами.
        \n Синтаксис: !таланты [опции]\
        \n -п >>> текущая справка по команде\
        """

        file_directory = '/home/Moldus/vkbot/genshin/boss_materials/materials.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'data': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    @genshinwrap.get_ps_pictures
    def get_books(api, chat_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=knigi
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с изображением таблицы формата \
        «дни недели-доступные для фарма книги».
        \n Синтаксис: !книги [опции]\
        \n -п >>> текущая справка по команде\
        """

        file_directory = '/home/Moldus/vkbot/genshin/books/книги.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'data': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    @genshinwrap.get_ps_pictures
    def get_domains(api, chat_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=danzhi
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с изображением игровых подземелий \
        с их дропом, мобами и дебаффами подземелья.
        \n Синтаксис: !данжи [опции]\
        \n -п >>> текущая справка по команде\
        """

        file_directory = '/home/Moldus/vkbot/genshin/dungeons/dungeon.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'data': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}


class HoYoLAB:
    def __init__(self):
        self.accounts = {}

    def load_accounts(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/accounts/accounts.pkl', 'rb') as accounts:
            self.accounts = pickle.load(accounts)
            return 1

    def dump_accounts(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/accounts/accounts.pkl', 'wb') as accounts:
            pickle.dump(self.accounts, accounts)
            return 1

    @genshinwrap.register_in_gdb
    def register_in_gdb(self, user_id: int, raw: str):
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=genshreg
        \n Описание: Данная команда позволяет зарегистрировать свой игровой аккаунт в базе данных бота.\
        \n Требуемые данные: [ltoken], [ltuid], [cookie_token], [uid]
        \n Примечание 1: после регистрации бот автоматически будет собирать логин-бонус для вашего аккаунта на сайте \
        HoYoLab. Происходить это будет раз в 8 часов вечера по Московскому времени.\
        \n Примечание 2: если после регистрации в базе вы решите сменить свои внутриигровые данные, то процесс \
        регистрации придется проводить по новой, т.к. при их смене ваши куки меняются.
        \n Синтаксис: !геншрег [опции] [данные=значение]\
        \n -п >>> текущая справка по команде
        """

        if user_id in self.accounts:
            return {'error': 'Ваш аккаунт уже существует в базе!'}

        data = {}
        try:
            assert len(raw.split()) == 4
            for elem in raw.split():
                data[elem.lower().split('=')[0]] = elem.split('=')[1]
            assert {'ltuid', 'ltoken', 'uid', 'cookie_token'} == set(data)
        except (AssertionError, IndexError):
            return {'error': 'Ошибка: не все данные указаны, или при их указании нарушен синтаксис!'}

        self.accounts[user_id] = data
        self.accounts[user_id]['resin_notify'] = False
        self.dump_accounts()
        return {'data': 'Регистрация прошла успешно!'}

    @genshinwrap.remove_data_from_gdb
    def remove_data_from_gdb(self, user_id: int):
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=genshdel
        \n Описание: Данная команда удаляет ваш игровой аккаунт из базы данных бота.
        \n Синтаксис: !геншдел [опции]\
        \n -п >>> текущая справка по команде
        """

        if user_id not in self.accounts:
            return {'error': 'Неудачная попытка воспользоваться командой, т.к. вас нет в базе!'}

        del self.accounts[user_id]
        self.dump_accounts()
        return {'data': 'Ваши данные были успешно удалены!'}

    @genshinwrap.get_notes
    def get_notes(self, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=zametki
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с вашими заметками \
        путешественника в реальном времени.
        \n Синтаксис: !заметки [опции]\
        \n -п >>> текущая справка по команде\
        \n -у [ответ на сообщение другого игрока] >>> просмотр заметок другого путешественника
        """

        notes = {}
        try:
            notes['data'] = templates.genshin.HoYoLAB.notes(gs.get_notes(
                uid=self.accounts[user_id]['uid'], lang='ru-ru',
                cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
            ))
        except gs.errors.GenshinStatsException as exc:
            notes['error'] = f"Ошибка: {exc}"
        except KeyError:
            notes['error'] = 'Ошибка: в базе отсутствуют ваши данные!'
        return notes

    @genshinwrap.get_daily_reward
    def get_daily_reward(self, api, chat_id: int, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=nagrady
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с информацией о ваших \
        логин-бонусах.
        \n Синтаксис: !награды [опции]\
        \n -п >>> текущая справка по команде
        """

        rewards = []
        try:
            rewards.append(gs.get_claimed_rewards(
                cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
            ))
            rewards.append(gs.claim_daily_reward(
                uid=self.accounts[user_id]['uid'], lang='ru-ru',
                cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
            ))
        except gs.errors.GenshinStatsException as exc:
            return {'message': f"Ошибка: {exc}"}
        except KeyError:
            return {'message': 'Ошибка: в базе отсутствуют ваши данные!'}

        info = templates.genshin.HoYoLAB.rewards(rewards)
        icon_link = api.vk.files.get_files_id(
            api.vk.files.upload_file(
                chat_id, api.vk.files.download_file(info['icon_link'], 'photo', 'jpg', cache=True), 'photo'
            )
        )
        return {'message': '\n'.join([info['title'], info['rewards']]), 'attachments': icon_link}

    @genshinwrap.get_stats
    def get_stats(self, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=staty
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с вашей внутриигровой статистикой.
        \n Синтаксис: !статы [опции]\
        \n -п >>> текущая справка по команде\
        \n -у [ответ на сообщение другого игрока] >>> просмотр внутриигровой статистики другого путешественника
        """

        stats = []
        try:
            stats.append(gs.get_user_stats(
                uid=self.accounts[user_id]['uid'], lang='ru-ru',
                cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
            ))
        except gs.errors.GenshinStatsException as exc:
            return {'error': f"Ошибка: {exc}"}
        except KeyError:
            return {'error': 'Ошибка: в базе отсутствуют ваши данные!'}
        return {'data': templates.genshin.HoYoLAB.stats(stats[0])}

    @genshinwrap.activate_redeem
    def activate_redeem(self, user_id: int, raw: str) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=prom
        \n Описание: При использовании данной команды команды бот активирует на вашем игровом аккаунте указанные в \
        теле сообщения промокоды.
        \n Примечание: промокоды вводятся через пробел.
        \n Синтаксис: !пром [опции] [промокод-1] [промокод-2] [промокод-n]\
        \n -п >>> текущая справка по команде
        """

        if not raw:
            return {'error': 'Ошибка: не указан ни один промокод!'}
        response = []
        codes = raw.split() if raw.find(' ') != -1 else [raw]

        for code in codes:
            try:
                gs.redeem_code(code=code, uid=self.accounts[user_id]['uid'],
                               cookie=gs.set_cookie(account_id=self.accounts[user_id]['ltuid'],
                                                    cookie_token=self.accounts[user_id]['cookie_token']))
                response.append(f"Успешно активирован промокод {code}!")
            except KeyError:
                return {'error': 'Ошибка: в базе отсутствуют ваши данные!'}
            except gs.errors.GenshinStatsException as e:
                response.append(f"Ошибка при активации промокода {code}: {e}")
            sleep(5)
        return {'data': '\n'.join(response)}

    def notify_about_resin(self, api) -> None:
        cases = {1: 'у', 2: 'ы', 3: 'ы', 4: 'ы'}
        self.load_accounts()
        api.vk.chats.load()

        for user_id in self.accounts:
            user = self.accounts[user_id]
            if user['resin_notify']:
                try:
                    resin = gs.get_notes(
                        uid=user['uid'], cookie=gs.set_cookie(ltuid=user['ltuid'], ltoken=user['ltoken'])
                    )['resin']
                except gs.errors.GenshinStatsException:
                    resin = 0
                    api.vk.messages.send_(2000000004, f"Ошибка в оповещении на смолу: {traceback.format_exc()}")

                if resin >= 150:
                    for chat in api.vk.chats.chats['chats']:
                        if api.vk.chats.check_for_member(api, chat['id'], user_id):
                            api.vk.messages.send_(
                                chat['id'], message=f"@id{user_id} ({api.vk.get_username(user_id)}), ваша смола "
                                                    f"достигла отметки в {resin} единиц{cases.get(resin - 150, '')}, "
                                                    f"поспешите её потратить!"
                            )
        sleep(1800)

    @genshinwrap.manage_resin_notifications
    def manage_resin_notifications(self, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=rezinnout
        \n Описание: Данная команда может позволяет боту отмечать в чате пользователя, значение смолы которого \
        достигло или превысило 150 единиц.\
        \n Поведение по умолчанию для данной команды - отображение текущего статуса функции отметки пользователя в чате.
        \n Синтаксис: !резинноут [опции]\
        \n -п >>> текущая справка по команде\
        \n -выкл >>> выключение функции отметки пользователя в чате\
        \n -вкл >>> включение функции отметки пользователя в чате
        """

        response = {}
        try:
            response['data'] = (
                f"В данный момент у вас {'включены' if self.accounts[user_id]['resin_notify'] else 'отключены'} "
                f"оповещения о трате смолы!")
        except KeyError:
            response['error'] = 'Ошибка: в базе отсутствуют ваши данные!'
        return response

    def claim_daily_rewards(self, api) -> None:
        self.load_accounts()
        tz = datetime.timezone(datetime.timedelta(hours=3, minutes=0))
        hour = datetime.datetime.now(tz).hour
        minute = datetime.datetime.now(tz).minute

        if hour < 20:
            sleep((20 - hour)*3600 - minute*60)
        elif hour > 20:
            sleep((24 - hour + 20)*3600 - minute*60)
        else:
            for user_id in self.accounts:
                user = self.accounts[user_id]
                try:
                    gs.claim_daily_reward(
                        uid=user['uid'], cookie=gs.set_cookie(ltuid=user['ltuid'], ltoken=user['ltoken'])
                    )
                except gs.errors.GenshinStatsException:
                    api.vk.messages.send_(
                        2000000004, message=f"Ошибка в автосборе логин-бонуса: {traceback.format_exc()}"
                    )
            sleep(24*3600 - minute*60)


class Database:
    """Honey Impact data collection"""

    def __init__(self):
        self.characters = honeyimpact.Characters()
        self.weapons = honeyimpact.Weapons()
        self.artifacts = honeyimpact.Artifacts()
        self.enemies = honeyimpact.Enemies()
        self.books = honeyimpact.Books()

    @staticmethod
    @genshinwrap.get_database
    def get_started(api, chat_id: int, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=gdb
        \n Описание: При использовании данной команды бот отправляет в чат сообщение с интерактивной базой данных, \
        информация в которую загружается посредством парсинга сайта HoneyHunter.
        \n Синтаксис: !гдб [опции]\
        \n -п >>> текущая справка по команде
        """

        keyboard = api.vk.create_keyboard()

        keyboard.add_callback_button(
            label='Персонажи', color='primary', payload={'user_id': user_id, 'type': 'characters_elem'}
        )
        keyboard.add_line()

        keyboard.add_callback_button(
            label='Оружие', color='primary', payload={'user_id': user_id, 'type': 'weapons_type'}
        )
        keyboard.add_line()

        keyboard.add_callback_button(
            label='Артефакты', color='primary', payload={'user_id': user_id, 'type': 'artifacts_type'}
        )
        keyboard.add_line()

        keyboard.add_callback_button(
            label='Противники', color='primary', payload={'user_id': user_id, 'type': 'enemies_type'}
        )
        keyboard.add_line()

        keyboard.add_callback_button(
            label='Книги', color='primary', payload={'user_id': user_id, 'type': 'books', 'filter': 'Книги', 'page': 0}
        )
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': api.vk.files.get_files_id(
                api.vk.files.upload_file(chat_id, '/home/Moldus/vkbot/genshin/db_buttons/menu.png', 'photo', cache=True)
            ),
            'message': f"Доброго времени суток, {api.vk.get_username(user_id)}!"
        }
        return response

    @staticmethod
    def get_filters(api, chat_id: int, user_id: int, payloads: dict, payload_type: str) -> dict:
        buttons = 0
        keyboard = api.vk.create_keyboard()

        for i, f in enumerate(payloads['filters'][payload_type]):
            keyboard.add_line() if (buttons % 2 == 0 and buttons > 0) else None
            keyboard.add_callback_button(
                label=f, color='secondary',
                payload={'user_id': user_id, 'type': payload_type[:-5], 'filter': f, 'page': 0}
            )
            buttons += 1

        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': api.vk.files.get_files_id(
                api.vk.files.upload_file(
                    chat_id, f'/home/Moldus/vkbot/genshin/db_buttons/{payload_type}.png', 'photo', cache=True
                )
            )
        }
        return response

    @staticmethod
    def get_filtered_list(api, user_id: int, payloads: dict,
                          payload_type: str, filter_: str, page_: int) -> dict:
        keyboards = []
        buttons = 0
        page = 0
        keyboard = api.vk.create_keyboard()
        names = payloads['lists'][payload_type][filter_]

        for name in names:
            if name == list(names)[-1]:
                keyboard.add_line() if (buttons % 2 == 0 and buttons > 0) else None
                keyboard.add_callback_button(
                    label=name, color='secondary',
                    payload={'user_id': user_id, 'type': payload_type[:-1],
                             'filter': filter_, 'name': name, 'data': 'main'}
                )
                keyboard.add_line()
                if page != 0:
                    keyboard.add_callback_button(
                        label='Назад', color='primary',
                        payload={'user_id': user_id, 'type': payload_type, 'filter': filter_, 'page': page - 1}
                    )
                keyboard.add_callback_button(
                    label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'}
                )
                keyboards.append(keyboard.get_keyboard())
                break

            if buttons < 6:
                keyboard.add_line() if (buttons % 2 == 0 and buttons > 0) else None
                keyboard.add_callback_button(
                    label=name, color='secondary',
                    payload={
                        'user_id': user_id, 'type': payload_type[:-1], 'filter': filter_, 'name': name, 'data': 'main'
                    }
                )
                buttons += 1

            else:
                keyboard.add_line()
                keyboard.add_callback_button(
                    label=name, color='secondary',
                    payload={
                        'user_id': user_id, 'type': payload_type[:-1], 'filter': filter_, 'name': name, 'data': 'main'
                    }
                )
                keyboard.add_line()
                if page != 0:
                    keyboard.add_callback_button(
                        label='Назад', color='primary',
                        payload={'user_id': user_id, 'type': payload_type, 'filter': filter_, 'page': page - 1}
                    )

                keyboard.add_callback_button(
                    label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'}
                )
                page += 1
                keyboard.add_callback_button(
                    label='Далее', color='primary',
                    payload={'user_id': user_id, 'type': payload_type, 'filter': filter_, 'page': page}
                )
                keyboards.append(keyboard.get_keyboard())
                keyboard = api.vk.create_keyboard()
                buttons = 0
        response = {
            'keyboard': keyboards[page_],
            'message': f"Поиск по типу [{filter_}]: стр. {page_}"
        }
        return response

    def get_character(self, api, user_id: int, name: str, data: str, filter_: str) -> dict:
        messages = {
            'main': self.characters.get_information,
            'skills': self.characters.get_skills,
            'passives': self.characters.get_passives,
            'constellations': self.characters.get_constellations,
            'args': {'name': name, 'elem': filter_}
        }
        keyboard = api.vk.create_keyboard()
        buttons = templates.genshin.Database.character(user_id, name, filter_)

        for button in buttons:
            if data != button:
                keyboard.add_callback_button(**buttons[button])
                keyboard.add_line()

        keyboard.add_callback_button(
            label='К списку персонажей', color='primary',
            payload={'user_id': user_id, 'type': 'characters', 'filter': filter_, 'page': 0}
        )
        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})
        keyboard.add_line()
        keyboard.add_callback_button(
            label='К списку элементов', color='primary',
            payload={'user_id': user_id, 'type': 'characters_elem', 'filter': 'characters_elem'}
        )

        url = f"{self.characters.BASE_URL}img/char/{self.characters.characters[filter_][name]}.png"
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.characters.get_icon(api, url),
            'message': messages[data](**messages['args'])
        }
        return response

    def get_weapon(self, api, user_id: int, name: str, data: str, filter_: str) -> dict:
        messages = {
            'main': self.weapons.get_information,
            'ability': self.weapons.get_ability,
            'progression': self.weapons.get_progression,
            'story': self.weapons.get_story,
            'args': {'name': name, 'type_': filter_}
        }
        keyboard = api.vk.create_keyboard()
        buttons = templates.genshin.Database.weapon(user_id, name, filter_)

        for button in buttons:
            if data != button:
                keyboard.add_callback_button(**buttons[button])
                keyboard.add_line()

        keyboard.add_callback_button(
            label='К списку оружия', color='primary',
            payload={'user_id': user_id, 'type': 'weapons', 'filter': filter_, 'page': 0}
        )
        keyboard.add_line()
        keyboard.add_callback_button(
            label='К типам оружия', color='primary',
            payload={'user_id': user_id, 'type': 'weapons_type', 'filter': 'weapons_type'}
        )
        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})

        url = f"{self.weapons.BASE_URL}img/weapon/{self.weapons.weapons[filter_][name]['code']}.png"
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.weapons.get_icon(api, url),
            'message': messages[data](**messages['args'])
        }
        return response

    def get_artifact(self, api, user_id: int, name: str, filter_: str) -> dict:
        keyboard = api.vk.create_keyboard()
        keyboard.add_callback_button(
            label='К списку артефактов', color='primary',
            payload={'user_id': user_id, 'type': 'artifacts', 'filter': filter_, 'page': 0}
        )
        keyboard.add_line()
        keyboard.add_callback_button(
            label='К типам артефактов', color='primary',
            payload={'user_id': user_id, 'type': 'artifacts_type', 'filter': 'artifacts_type'}
        )
        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})

        url = f"{self.artifacts.artifacts[filter_][name]['icon']}"
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.artifacts.get_icon(api, url),
            'message': self.artifacts.get_information(name, filter_)
        }
        return response

    def get_enemy(self, api, user_id: int, name: str, data: str, filter_: str) -> dict:
        messages = {
            'main': self.enemies.get_information,
            'progression': self.enemies.get_progression,
            'args': {'name': name, 'type_': filter_}
        }
        keyboard = api.vk.create_keyboard()
        buttons = templates.genshin.Database.enemy(user_id, name, filter_)

        for button in buttons:
            if data != button:
                keyboard.add_callback_button(**buttons[button])
                keyboard.add_line()

        keyboard.add_callback_button(
            label='К списку противников', color='primary',
            payload={'user_id': user_id, 'type': 'enemies', 'filter': filter_, 'page': 0}
        )
        keyboard.add_line()
        keyboard.add_callback_button(
            label='К типам противников', color='primary',
            payload={'user_id': user_id, 'type': 'enemies_type', 'filter': 'enemies_type'}
        )
        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})

        url = f"{self.enemies.BASE_URL}img/enemy/{self.enemies.enemies[filter_][name]}.png"
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.enemies.get_icon(api, url),
            'message': messages[data](**messages['args'])
        }
        return response

    def get_book(self, api, user_id: int, name: str, data: str, volume: int, page_: int) -> dict:
        keyboard = api.vk.create_keyboard()
        keyboards = []
        buttons_ = 0
        page = 0
        buttons = templates.genshin.Database.book(user_id, name, self.books.get_volumes(name))

        for button in buttons:
            if button == list(buttons)[-1]:
                if data != button:
                    keyboard.add_callback_button(**buttons[button])
                    keyboard.add_line()
                keyboard.add_callback_button(label='К списку книг', color='primary',
                                             payload={'user_id': user_id, 'type': 'books',
                                                      'filter': 'Книги', 'page': 0})
                keyboard.add_line()
                if page != 0:
                    keyboard.add_callback_button(
                        label='Назад', color='primary',
                        payload={'user_id': user_id, 'type': 'book', 'name': name,
                                 'data': data, 'volume': volume, 'page': page - 1}
                    )
                keyboard.add_callback_button(
                    label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'}
                )
                keyboards.append(keyboard.get_keyboard())
                break
            if data != button:
                if buttons_ < 3:
                    keyboard.add_callback_button(**buttons[button])
                    keyboard.add_line()
                    buttons_ += 1
                else:
                    keyboard.add_callback_button(**buttons[button])
                    keyboard.add_line()
                    keyboard.add_callback_button(label='К списку книг', color='primary',
                                                 payload={'user_id': user_id, 'type': 'books',
                                                          'filter': 'Книги', 'page': 0})
                    keyboard.add_line()
                    if page != 0:
                        keyboard.add_callback_button(
                            label='Назад', color='primary',
                            payload={'user_id': user_id, 'type': 'book', 'name': name,
                                     'data': data, 'volume': volume, 'page': page - 1}
                        )
                    keyboard.add_callback_button(
                        label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'}
                    )
                    page += 1
                    keyboard.add_callback_button(
                        label='Далее', color='primary',
                        payload={'user_id': user_id, 'type': 'book', 'name': name,
                                 'data': data, 'volume': volume, 'page': page}
                    )
                    keyboards.append(keyboard.get_keyboard())
                    keyboard = api.vk.create_keyboard()
                    buttons_ = 0

        info = self.books.get_information(api, name, volume)
        attachments = self.books.get_icon(api, info[1])
        attachments.extend(info[2])
        response = {
            'keyboard': keyboards[page_],
            'message': info[0],
            'attachments': attachments
        }
        return response


class Genshin(Main):
    """Genshin class constructor"""

    def __init__(self):
        self.main = Main()
        self.hoyolab = HoYoLAB()
        self.db = Database()
