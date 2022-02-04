import random
from time import sleep
import pickle
import traceback
import datetime
import os

from pybooru import Danbooru
from simplejson.errors import JSONDecodeError
from vk_api.exceptions import VkApiError

import constants
import private
import templates.initial
import templates.vkontakte
import danboorutags


class Main:
    @staticmethod
    def get_guide() -> dict:
        return {'message': 'Список существующих команд: vk.com/@bot_genshin-commands'}

    @staticmethod
    def make_choice(raw: str) -> dict:
        options = raw.split('/') if raw.find('/') != -1 else []
        if '' in options or not options:
            return {'message': 'Не указаны варианты для выбора!'}
        return {'message': f"{random.choice(options)}"}

    @staticmethod
    def convert(reply_message: dict) -> dict:
        if not reply_message:
            return {'message': 'Вы не прикрепили сообщение, текст которого нужно конвертировать!'}

        text = reply_message['text'].lower()
        if not text:
            return {'message': 'Сообщение, которое вы прикрепили, не содержит текста!'}

        return {'message': ''.join([constants.Uncategorized.KEYBOARD.get(s, s) for s in text])}

    @staticmethod
    def set_timer(api, chat_id: int, user_id: int, username: str, raw: str) -> dict:
        time, note = (raw.split('/')[0], raw.split('/')[1]) if raw.find('/') != -1 else (raw, None)

        try:
            time = eval(time.replace('ч', '*3600+').replace('м', '*60+').replace('с', '*1+').strip().rpartition('+')[0])
            api.vk.messages.send_(chat_id=chat_id, message='Таймер установлен!')
        except (SyntaxError, NameError):
            return {'message': 'Ошибка при установке таймера: Синтаксис команды нарушен!'}

        sleep(time)
        return {'message': f"@id{user_id} ({username}), время прошло! {'Пометка: ' + note if note else ''}"}

    @staticmethod
    def send_attachments(api, attachments: list) -> dict:
        if not attachments:
            return {'message': 'Невозможно переслать медиавложения, если они не указаны!'}
        else:
            return {'attachments': api.vk.files.get_files_id(attachments)}


class Booru:
    def __init__(self):
        self.api = Danbooru('danbooru', username=private.Danbooru.USERNAME, api_key=private.Danbooru.USER_TOKEN)

    @staticmethod
    def get_randtags(raw: str) -> dict:
        try:
            amount = int(raw.strip())
        except ValueError:
            return {'message': 'Ошибка в указании количества тегов!'}
        if amount <= 200:
            return {'message': '\n'.join([random.choice(list(danboorutags.tags)) for _ in range(amount)])}
        else:
            return {'message': 'Можно выполнить генерацию не более 200 тегов за раз!'}

    def get_randpics(self, api, chat_id: int, raw: str) -> dict:
        try:
            amount = int(raw.split(maxsplit=1)[0])
            raw_tags = raw.split(maxsplit=1)[1].split() if not raw.isdigit() else []
        except (ValueError, IndexError):
            return {'message': 'Ошибка в указании количества изображений!'}
        if len(raw_tags) > 4:
            return {'message': 'Нельзя указать более 4 тегов одновременно!'}

        amount = abs(amount) if abs(amount) <= 10 else 10
        errors = []
        tags = []

        for tag in raw_tags:
            if tag[0] != '-' and tag in danboorutags.tags:
                tags.append(danboorutags.tags.get(tag, ''))
            elif tag[0] == '-' and tag[1:] in danboorutags.tags:
                tags.append(f"-{danboorutags.tags.get(tag[1:], '')}")
            else:
                errors.append(tag)

        if errors:
            return {'message': f"Указанные теги не существуют: {', '.join(errors)}"}

        pics = random.choices(
            self.api.post_list(random=True, limit=amount+10, tags=f"rating:s {' '.join(tags)}"), k=amount
        )
        pic_arrays = []
        for pic in pics:
            pic_arrays.extend(
                api.vk.files.upload_file(
                    chat_id, api.vk.files.download_file(pic['large_file_url'], 'photo', pic['file_ext'], cache=True),
                    'photo'
                )
            )

        response = {
            'message': f"По вашему запросу найдено {len(pic_arrays)} изображений!",
            'attachments': api.vk.files.get_files_id(pic_arrays)
        }
        return response


class UserCommands:
    def __init__(self):
        self.commands = {}

    def load(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/user_commands/usercoms.pkl', 'rb') as commands:
            self.commands = pickle.load(commands)
            return 1

    def dump(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/user_commands/usercoms.pkl', 'wb') as commands:
            pickle.dump(self.commands, commands)
        return 1

    def _is_exists(self, chat_id: int) -> int:
        if chat_id not in self.commands:
            self.commands[chat_id] = {}
            self.commands[chat_id]['ffa'] = True
            self.commands[chat_id]['commands'] = {}
        return 1

    def get(self, chat_id: int) -> dict:
        if chat_id < 2 * (10 ** 9):
            return {'message': 'Данная функция недоступна для использования в личных сообщениях!'}
        elif chat_id not in self.commands or not self.commands.get(chat_id, {}).get('commands'):
            return {'message': 'В этом чате не создано ни одной команды!'}

        return {'message': 'Список пользовательских команд:\n' + '\n'.join(list(self.commands[chat_id]['commands']))}

    def add(self, api, chat_id: int, user_id: int, raw: str, attachments: list) -> dict:
        general_commands = constants.Uncategorized.COMMANDS

        if chat_id < 2 * (10 ** 9):
            return {'message': 'Данная функция недоступна для использования в личных сообщениях!'}
        if not raw or (len(raw.split()) == 1 and not attachments):
            return {'message': 'Вы не можете добавить команду без названия и описания!'}

        name, message = (raw.split(maxsplit=1)[0], raw.split(maxsplit=1)[1]) if raw.find(' ') != -1 else (raw, '')
        self._is_exists(chat_id)

        if name in self.commands[chat_id]['commands'] or name in general_commands:
            return {'message': 'Данная команда уже существует!'}
        elif not self.commands[chat_id]['ffa'] and not api.vk.chats.check_for_privileges(api, chat_id, user_id):
            return {'message': 'У вас недостаточно прав для добавления данной команды!'}

        date = datetime.datetime.now()
        date = f"{date.day}.{date.month}.{date.year}"
        creator = api.vk.group_api.users.get(user_ids=user_id)[0]['id']
        path = f"/home/Moldus/vkbot/genshin/user_commands/files/chat_{chat_id}/"
        if not os.path.isdir(path):
            os.mkdir(path)

        self.commands[chat_id]['commands'][name] = {
            'args': {'message': message, 'attachments': []},
            'info': {'date_added': date, 'creator': f"id{creator}", 'times_used': 0}
        }

        for attachment in attachments:
            if attachment['type'] == 'audio':
                self.commands[chat_id]['commands'][name]['args']['attachments'].extend(
                    api.vk.files.get_files_id([attachment])
                )
            elif attachment['type'] == 'photo':
                url = {s['height']: s['url'] for s in attachment['photo']['sizes']}
                url = url[max(url)]
                api.vk.files.download_file(url, 'photo',  'jpg', f"{path}{name}.jpg", cache=True)
            elif attachment['type'] == 'doc':
                ext = attachment['doc']['ext']
                url = attachment['doc']['url']
                self.commands[chat_id]['commands'][name]['args']['attachments'].extend(
                    api.vk.files.get_files_id(
                        api.vk.files.upload_file(
                            chat_id, api.vk.files.download_file(url, 'doc', ext, cache=True), 'doc', name
                        )
                    )
                )

        self.dump()
        return {'message': f"Команда {name} успешно добавлена!"}

    def delete(self, api, chat_id: int, user_id: int, name: str) -> dict:
        if chat_id < 2 * (10 ** 9):
            return {'message': 'Данная функция недоступна для использования в личных сообщениях!'}
        elif chat_id not in self.commands:
            return {'message': 'В этом чате не создано ни одной команды!'}
        elif not name:
            return {'message': 'Вы не можете удалить команду без указания ее названия!'}

        if name not in self.commands[chat_id]['commands']:
            return {'message': 'Вы не можете удалить несуществующую команду!'}
        elif not self.commands[chat_id]['ffa'] and not api.vk.chats.check_for_privileges(api, chat_id, user_id):
            return {'message': 'У вас недостаточно прав для удаления данной команды!'}

        path = f"/home/Moldus/vkbot/genshin/user_commands/files/chat_{chat_id}/"
        for file in os.listdir(path):
            os.remove(f"{path}{file}") if file.startswith(f"{name}.") else None
        del self.commands[chat_id]['commands'][name]

        self.dump()
        return {'message': f"Команда {name} успешно удалена!"}

    def send(self, api, chat_id: int, name: str) -> list:
        type_ = constants.Extensions.EXT
        path = f"/home/Moldus/vkbot/genshin/user_commands/files/chat_{chat_id}/"
        attachments = []
        attachments.extend(self.commands[chat_id]['commands'][name]['args']['attachments'])
        message = self.commands[chat_id]['commands'][name]['args']['message']
        self.commands[chat_id]['commands'][name]['info']['times_used'] += 1

        for file in os.listdir(path):
            if file.startswith(f"{name}."):
                attachments.extend(
                    api.vk.files.get_files_id(
                        api.vk.files.upload_file(chat_id, f"{path}{file}", type_[file.split('.')[-1]], cache=True)
                    )
                )

        self.dump()
        return api.vk.messages.send_(chat_id, message, attachments)

    def switch(self, api, chat_id: int, user_id: int) -> dict:
        if api.vk.chats.check_for_privileges(api, chat_id, user_id):
            self.commands[chat_id]['ffa'] = True if not self.commands[chat_id]['ffa'] else False
            self.dump()
            return {'message': 'Изменены права на изменение пользовательских команд в чате!'}
        else:
            return {'message': 'Для использования данной команды требуется быть администратором чата!'}


class Initial(Main):
    """Initial class constructor"""

    def __init__(self):
        self.booru = Booru()
        self.usercoms = UserCommands()

        self.recently_posted = {}
        self.tags = ''
        self.thematic = False

    def load_recently_posted(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/recently_posted/pictures.pkl', 'rb') as recently_posted:
            self.recently_posted = pickle.load(recently_posted)
            return 1

    def dump_recently_posted(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/recently_posted/pictures.pkl', 'wb') as recently_posted:
            pickle.dump(self.recently_posted, recently_posted)
            return 1

    def _insert_post_ids(self, post_id: dict, picture, donut: bool) -> int:
        post_type = 'common' if not donut else 'donut'
        self.recently_posted[post_type]['vk_ids'].append(post_id['post_id'])
        self.recently_posted[post_type]['ids'].append(picture['id'])
        return 1

    def _is_pic_exists(self, pic: dict) -> bool:
        status = False

        if (pic and pic['id'] not in self.recently_posted['common']['ids']
                and pic['id'] not in self.recently_posted['donut']['ids']):
            status = True
        return status

    def _get_picture(self, limit: int, thematic: bool, donut: bool) -> dict:
        status = False
        response = {}

        while not status:
            pictures = self.booru.api.post_list(
                random=True, limit=limit,
                tags=(f"genshin_impact -filetype:mp4 rating:{'s' if not donut else 'q'} "
                      f"{'' if not donut else '-loli'} {self.tags}")
            )
            picture = templates.initial.Initial.primary_sorting(pictures)

            if not self._is_pic_exists(picture):
                continue

            picture = templates.initial.Initial.secondary_sorting(picture, donut=donut)

            if not picture:
                continue
            elif thematic and not len(picture['characters']) <= 3:
                continue
            response = picture
            status = True

        return response

    def make_post(self, api, limit: int = 10, donut=False) -> int:
        """Service use only"""

        self.load_recently_posted()
        status = False

        while not status:
            picture = self._get_picture(limit, self.thematic, donut=donut)
            message = templates.initial.Initial.get_message(picture, donut=donut)

            args = {
                'owner_id': -private.Vk.GROUP_ID, 'message': message,
                'close_comments': 0, 'copyright': picture['original_url']
            }

            try:
                picture_id = api.vk.files.get_files_id(
                    api.vk.files.upload_file(
                        private.Vk.GROUP_ID,
                        api.vk.files.download_file(picture['resized_url'], 'photo_wall', picture['ext'], cache=True),
                        'photo_wall'
                    )
                )
                args['attachments'] = picture_id
                if donut:
                    args['donut_paid_duration'] = -1

                post_id = api.vk.user_api.wall.post(**args)
                self._insert_post_ids(post_id, picture, donut=donut)
                self.dump_recently_posted()
                status = True
            except JSONDecodeError:
                continue
            except VkApiError:
                api.vk.messages.send_(2000000004, f"{str(picture)}\n{traceback.format_exc()}"[:4096])
        return 1
