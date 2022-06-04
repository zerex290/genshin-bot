from typing import Tuple


__all__ = (
    'GenshinBotException',
    'IncompatibleOptions'
)


class GenshinBotException(Exception):
    _msg = ''

    @property
    def msg(self) -> str:
        return f"Ошибка: {self._msg}"


class IncompatibleOptions(GenshinBotException):
    def __init__(self, options: Tuple[str, ...]) -> None:
        self.__class__._msg = f"Переданы несовместимые опции: {' '.join(options)}!"
