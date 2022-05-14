from vkbottle.bot import Message

from bot.errors import GenshinBotException


__all__ = ('BaseValidator',)


class BaseValidator:
    def __init__(self, message: Message) -> None:
        self._message = message

    async def __aenter__(self) -> 'BaseValidator':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        if not exc_type:
            return True
        if issubclass(exc_type, GenshinBotException):
            await self._message.answer(exc_val.msg)
            return True
        return False
