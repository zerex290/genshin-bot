from typing import List


class GenshinBotException(Exception):
    _msg = ''

    @property
    def msg(self) -> str:
        return f"Ошибка: {self._msg}"


class IncompatibleOptions(GenshinBotException):
    def __init__(self, options: List[str]) -> None:
        self.__class__._msg = f"Переданы несовместимые опции: {', '.join(options)}!"


class WrongChatError(GenshinBotException):
    _msg = 'Использование данной команды в личных сообщениях группы невозможно!'
