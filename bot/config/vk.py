from vkbottle import API, Bot, User

from .dependencies import user
from .dependencies import group


class Vk:
    @staticmethod
    def get_group_session() -> Bot:
        api = API(group.TOKEN)
        return Bot(api=api)

    @staticmethod
    def get_user_session() -> User:
        api = API(user.TOKEN)
        return User(api=api)
