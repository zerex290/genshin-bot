from vkbottle import API, Bot, User

from bot.config.dependencies import user
from bot.config.dependencies import group


class Vk:
    __slots__ = ['_group_token', '_group_id', '_user_token', '_user_id']

    def __init__(self) -> None:
        self._group_token = group.TOKEN
        self._group_id = group.ID

        self._user_token = user.TOKEN
        self._user_id = user.ID

    def get_group_session(self) -> Bot:
        api = API(self._group_token)
        return Bot(api=api)

    def get_user_session(self) -> User:
        api = API(self._user_token)
        return User(api=api)
