from bot.config import Vk


class Bot(Vk):
    __slots__ = ['group', 'user', 'auth_type']

    def __init__(self) -> None:
        super().__init__()
        self.group = self.get_group_session()
        self.user = self.get_user_session()
