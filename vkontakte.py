import os
import random
import pickle

import requests

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id

import templates.vkontakte


class Session:
    def __init__(self, group_token, group_id, user_token, app_id, client_secret, scope):
        self._group_token = group_token
        self._group_id = group_id
        self.event_type = VkBotEventType

        self._scope = scope
        self._client_secret = client_secret
        self._app_id = app_id
        self._user_token = user_token

        self.group, self.group_api = self._group_session()
        self.user, self.user_api = self._user_session()

    def _group_session(self):
        """Service use only"""

        group_session = vk_api.vk_api.VkApiGroup(token=self._group_token, api_version='5.131')
        return group_session, group_session.get_api()

    def _user_session(self):
        """Service use only"""

        user_session = vk_api.VkApi(api_version='5.131', scope=self._scope, client_secret=self._client_secret,
                                    app_id=self._app_id, token=self._user_token)
        return user_session, user_session.get_api()


class Messages:
    def __init__(self, api):
        self._api = api

        self.raw = None
        self.action = None
        self.user_id = None
        self.chat_id = None
        self.message = None
        self.attachments = None
        self.reply_message = None
        self.fwd_messages = None
        self.prefix = None
        self.trigger = None

    def components(self, event) -> dict:
        """Service use only"""

        self.raw = event
        self.action = self.raw.obj['message'].get('action', {}).get('type', {})
        self.user_id = self.raw.obj['message']['from_id']
        self.chat_id = self.raw.obj['message']['peer_id']
        self.message = self.raw.obj['message']['text']
        self.attachments = self.raw.obj['message']['attachments']
        self.reply_message = self.raw.obj['message'].get('reply_message', {})
        self.fwd_messages = self.raw.obj['message']['fwd_messages']
        self.prefix = (True if self.message[0] == '!' else False) if self.message else False
        self.trigger = self.message.split()[0][1:] if self.prefix else ''

        response = {
            'raw': self.raw,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message': self.message,
            'attachments': self.attachments,
            'reply_message': self.reply_message,
            'fwd_messages': self.fwd_messages,
            'prefix': self.prefix,
            'trigger': self.trigger
        }
        return response

    def send_(self, chat_id, message=None, attachments=None, keyboard=None, sticker=None, fwd_messages=None) -> dict:
        """Service use only"""

        response = self._api.messages.send(
            peer_ids=chat_id, message=message, attachment=attachments, sticker_id=sticker,
            forward_messages=fwd_messages, keyboard=keyboard, random_id=get_random_id()
        )
        return response

    def edit_(self, chat_id, conversation_message_id, message=None, attachments=None, keyboard=None):
        """Service use only"""

        self._api.messages.edit(
            peer_id=chat_id, conversation_message_id=conversation_message_id,
            message=message, attachment=attachments, keyboard=keyboard
        )
        return 1


class Files:
    def __init__(self, session):
        self.upload = VkUpload(session)
        self.attachment_types = templates.vkontakte.Files.ATTACHMENT_TYPES
        self.upl_types = templates.vkontakte.Files.UPLOAD_TYPES

    def get_files_id(self, attachments: list) -> list or None:
        """Service use only"""

        id_ = []

        for attachment in attachments:
            if attachment['type'] in self.attachment_types:
                id_.append(self.attachment_types[attachment['type']](attachment[attachment['type']]))

        return id_ if id_ else None

    @staticmethod
    def download_file(url: str, type_: str, ext: str, dir_: str = None, cache: bool = False) -> str:
        """Service use only"""

        file_directory = f"/home/Moldus/vkbot/cache/{type_}_{random.randint(0, 10)}.{ext}" if dir_ is None else dir_

        with open(file_directory, 'wb') as file:
            file.write(requests.get(url).content)

        if not cache:
            os.remove(file_directory)
        return file_directory

    def upload_file(self, peer: int, dir_: str, type_: str, title: str = None, cache: bool = False) -> list:
        """Service use only"""

        try:
            if type_ != 'doc':
                file = {type_: self.upl_types[type_](self.upload, dir_, peer)[0], 'type': type_}
            else:
                file = self.upl_types['doc'](self.upload, dir_, peer, title)
        except vk_api.exceptions.ApiError:
            file = {}

        if not cache:
            os.remove(dir_)
        return [file]


class Chats:
    def __init__(self):
        self.chats = {}

    def load(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/vk_chats/chats.pkl', 'rb') as chats:
            self.chats = pickle.load(chats)
            return 1

    def dump(self) -> int:
        """Service use only"""

        with open('/home/Moldus/vkbot/genshin/vk_chats/chats.pkl', 'wb') as chats:
            pickle.dump(self.chats, chats)
            return 1

    @staticmethod
    def get_chat_members(api, chat_id: int) -> list:
        """Service use only"""

        members = api.vk.group_api.messages.getConversationMembers(peer_id=chat_id)['items']
        return templates.vkontakte.Chats.members(members)

    def check_for_member(self, api, chat_id: int, user_id: int) -> bool:  #: не тестил
        """Service use only"""

        for mem in self.get_chat_members(api, chat_id):
            if mem['id'] == user_id:
                return True
        return False

    def check_for_privileges(self, api, chat_id: int, user_id: int) -> bool:
        """Service use only"""

        for mem in self.get_chat_members(api, chat_id):
            if mem['id'] == user_id and (mem.get('is_owner') or mem.get('is_admin')):
                return True
        return False

    def add_new_chat(self, api, chat_id: int) -> int:
        """Service use only"""

        self.chats['chats'].append(templates.vkontakte.Chats.new_chat(chat_id, self.get_chat_members(api, chat_id)))
        self.chats['ids'].append(chat_id)
        self.dump()
        return 1


class Vk(Session):
    """VK class constructor"""

    def __init__(self, group_token, group_id, user_token, app_id, client_secret, scope, auth_type):
        super().__init__(group_token, group_id, user_token, app_id, client_secret, scope)
        self._api = self.group_api if auth_type == 'group' else self.user_api

        self.messages = Messages(self._api)
        self.files = Files(self.group if auth_type == 'group' else self.user)
        self.chats = Chats()

    def get_username(self, user_id: int) -> str:
        """Service use only"""

        return self.group_api.users.get(user_ids=user_id)[0]['first_name']

    @staticmethod
    def create_keyboard(one_time=False, inline=True) -> VkKeyboard:
        """Service use only"""

        keyboard = VkKeyboard(one_time=one_time, inline=inline)
        return keyboard

    @staticmethod
    def get_longpoll_server(session, group_id=None, auth_type='group'):
        """Service use only"""

        client_type = {'group': VkBotLongPoll, 'user': VkLongPoll}
        return client_type[auth_type](vk=session, group_id=group_id)
