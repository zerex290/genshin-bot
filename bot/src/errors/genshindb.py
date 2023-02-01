from . import GenshinBotException


__all__ = (
    'ShortcutNotSpecified',
    'ShortcutAlreadyExist',
    'ShortcutNotExist',
    'ReplyMessageError',
    'WrongReplyMessage',
    'ShortcutsNotCreated'
)


class ShortcutNotSpecified(GenshinBotException):
    _msg = 'Вы не указали название для шортката!'


class ShortcutAlreadyExist(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"У вас уже существует шорткат '{name}'!"


class ShortcutNotExist(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"Не найден шорткат с именем '{name}'!"


class ReplyMessageError(GenshinBotException):
    _msg = 'Вы не прикрепили сообщение, на которое хотите установить пользовательский шорткат!'


class WrongReplyMessage(GenshinBotException):
    _msg = 'Сообщение, которое вы прикрепили, не является сообщением с интерактивной базой данных!'


class ShortcutsNotCreated(GenshinBotException):
    _msg = 'У вас не создано ни одного шортката!'
