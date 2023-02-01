from importlib import import_module
from types import ModuleType

from vkbottle import API, Bot, User
from vkbottle.bot import BotLabeler

from .dependencies import user
from .dependencies import group


__all__ = ('bot',)


class GenshinBot:
    _labeler = BotLabeler()

    def __init__(self):
        self.group = Bot(api=API(group.TOKEN), labeler=self._labeler)
        self.user = User(api=API(user.TOKEN), labeler=self._labeler)

    def load_labelers(self) -> 'GenshinBot':
        handlers: ModuleType = import_module('...handlers', __name__)
        for labeler in handlers.__all__:
            self._labeler.load(getattr(handlers, labeler))
        return self

    def register_middlewares(self) -> 'GenshinBot':
        middlewares: ModuleType = import_module('...middlewares', __name__)
        for middleware in middlewares.__all__:
            self._labeler.message_view.register_middleware(getattr(middlewares, middleware))
        return self


bot = GenshinBot()
