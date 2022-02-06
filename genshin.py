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
    def get_daily_farm(api, chat_id: int) -> dict:
        file_directory = f"/home/Moldus/vkbot/genshin/daily_farm/{datetime.datetime.now().weekday()}.png"
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'attachments': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    def get_ascension_materials(api, chat_id: int, character: str) -> dict:
        if not character:
            return {'message': 'Вы не указали имя персонажа!'}
        file_directory = constants.Genshin.ASCENSION.get(character.replace(' ', ''), None)
        if not file_directory:
            return {'message': f"Ошибка в имени персонажа {character}!"}
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'attachments': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    def get_boss_materials(api, chat_id: int) -> dict:
        file_directory = '/home/Moldus/vkbot/genshin/boss_materials/materials.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'attachments': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    def get_books(api, chat_id: int) -> dict:
        file_directory = '/home/Moldus/vkbot/genshin/books/книги.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'attachments': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}

    @staticmethod
    def get_domains(api, chat_id: int) -> dict:
        file_directory = '/home/Moldus/vkbot/genshin/dungeons/dungeon.png'
        pic = api.vk.files.upload.photo_messages(file_directory, peer_id=chat_id)
        return {'attachments': [f"photo{pic[0]['owner_id']}_{pic[0]['id']}_{pic[0]['access_key']}"]}


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

    def register_in_gdb(self, user_id: int, raw: str):
        if user_id in self.accounts:
            return {'message': 'Ваш аккаунт уже существует в базе!'}

        data = {}
        try:
            assert len(raw.split()) == 4
            for elem in raw.split():
                data[elem.lower().split('=')[0]] = elem.split('=')[1]
            assert 'ltuid' and 'ltoken' and 'cookie_token' and 'uid' in data
        except (AssertionError, IndexError):
            return {'message': 'Ошибка: не все данные указаны, или при их указании нарушен синтаксис!'}

        self.accounts[user_id] = data
        self.accounts[user_id]['resin_notify'] = False
        self.dump_accounts()
        return {'message': 'Регистрация прошла успешно!'}

    def remove_data_from_gdb(self, user_id: int):
        if user_id not in self.accounts:
            return {'message': 'Неудачная попытка воспользоваться командой, т.к. вас нет в базе!'}

        del self.accounts[user_id]
        self.dump_accounts()
        return {'message': 'Ваши данные были успешно удалены!'}

    # @genshinwrap.get_notes
    # def get_notes(self, user_id: int) -> dict:
    #     notes = []
    #
    #     try:
    #         notes.append(gs.get_notes(
    #             uid=self.accounts[user_id]['uid'], lang='ru-ru',
    #             cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
    #         ))
    #     except gs.errors.GenshinStatsException as exc:
    #         return {'message': f"Ошибка: {exc}"}
    #     except KeyError:
    #         return {'message': 'Ошибка: в базе отсутствуют ваши данные!'}
    #     return {'message': templates.genshin.HoYoLAB.notes(notes[0])}

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

    def get_daily_reward(self, api, chat_id: int, user_id: int) -> dict:
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

    def get_stats(self, user_id: int) -> dict:
        stats = []

        try:
            stats.append(gs.get_user_stats(
                uid=self.accounts[user_id]['uid'], lang='ru-ru',
                cookie=gs.set_cookie(ltuid=self.accounts[user_id]['ltuid'], ltoken=self.accounts[user_id]['ltoken'])
            ))
        except gs.errors.GenshinStatsException as exc:
            return {'message': f"Ошибка: {exc}"}
        except KeyError:
            return {'message': 'Ошибка: в базе отсутствуют ваши данные!'}
        return {'message': templates.genshin.HoYoLAB.stats(stats[0])}

    def activate_redeem(self, user_id: int, raw: str) -> dict:
        if not raw:
            return {'message': 'Ошибка: не указан ни один промокод!'}
        response = []
        codes = raw.split() if raw.find(' ') != -1 else [raw]

        for code in codes:
            try:
                gs.redeem_code(code=code, uid=self.accounts[user_id]['uid'],
                               cookie=gs.set_cookie(account_id=self.accounts[user_id]['ltuid'],
                                                    cookie_token=self.accounts[user_id]['cookie_token']))
                response.append(f"Успешно активирован промокод {code}!")
            except KeyError:
                return {'message': 'Ошибка: в базе отсутствуют ваши данные!'}
            except gs.errors.GenshinStatsException as e:
                response.append(f"Ошибка при активации промокода {code}: {e}")
            sleep(5)
        return {'message': '\n'.join(response)}

    def notify_about_resin(self, api) -> None:
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
                                                    f"достигла отметки в {resin} единиц, поспешите её потратить!"
                            )
        sleep(1800)

    # def switch_resin_notifications(self, user_id: int, raw: str) -> dict:
    #     if raw.find('вкл') != -1:
    #         self.accounts[user_id]['resin_notify'] = True
    #         self.dump_accounts()
    #         return {'message': 'Автоматическое напоминание потратить смолу включено!'}
    #     elif raw.find('выкл') != -1:
    #         self.accounts[user_id]['resin_notify'] = False
    #         self.dump_accounts()
    #         return {'message': 'Автоматическое напоминание потратить смолу отключено!'}
    #     else:
    #         return {'message': 'Неправильно указаны агрументы для команды!'}

    @genshinwrap.switch_resin_notifications
    def switch_resin_notifications(self, user_id: int) -> dict:
        """
        \n Ссылка на команду в статье: https://vk.com/@bot_genshin-commands?anchor=rezinnout
        \n Описание: Данная команда может проводить манипуляции с функцией отметки в чате пользователя, значение смолы \
        которого достигло или превысило 150 единиц.\
        \n По умолчанию показывает текущий статус функции отметки в чате.
        \n Синтаксис: !резинноут [опции]\
        \n -п >>> текущая справка по команде\
        \n -выкл >>> выключение функции отметки в чате\
        \n -вкл >>> включение функции отметки в чате
        """

        response = {}
        try:
            response['data'] = (
                f"В данный момент у вас {'включены' if self.accounts[user_id]['resin_notify'] else 'отключены'} "
                f"оповещения о трате смолы!")
        except KeyError:
            response['error'] = f"Ошибка: в базе отсутствуют ваши данные!"
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

    @staticmethod
    def get_started(api, chat_id: int, user_id: int) -> dict:
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
        keyboard.add_callback_button(
            label='К списку стихий', color='primary',
            payload={'user_id': user_id, 'type': 'characters_elem', 'filter': 'characters_elem'}
        )
        keyboard.add_line()
        keyboard.add_callback_button(label='Меню', color='positive', payload={'user_id': user_id, 'type': 'menu'})
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.characters.get_icon(api, name, filter_),
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
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.weapons.get_icon(api, name, filter_),
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
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.artifacts.get_icon(api, name, filter_),
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
        response = {
            'keyboard': keyboard.get_keyboard(),
            'attachments': self.enemies.get_icon(api, name, filter_),
            'message': messages[data](**messages['args'])
        }
        return response


class Genshin(Main):
    """Genshin class constructor"""

    def __init__(self):
        self.main = Main()
        self.hoyolab = HoYoLAB()
        self.db = Database()
