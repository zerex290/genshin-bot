from vkbottle.bot import Message

from bot.errors import GenshinBotException, WrongChatError


__all__ = (
    'BaseValidator',
    'ChatValidator'
)


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


class ChatValidator:
    """Mixin class"""
    @staticmethod
    def check_chat_allowed(chat_id: int) -> None:
        if chat_id < 2e9:
            raise WrongChatError
