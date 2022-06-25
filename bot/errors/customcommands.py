from bot.errors import GenshinBotException


__all__ = (
    'CommandsNotCreated',
    'AvailabilityError',
    'ActionsAlreadyPublic',
    'ActionsAlreadyRestricted',
    'ActionError',
    'CommandNotSpecified',
    'CommandAlreadyExist',
    'CommandNotExist',
    'CommandReserved',
    'AdditionsNotSpecified',
    'BotPrivilegesError'
)


class CommandsNotCreated(GenshinBotException):
    _msg = 'В данном чате не создано ни одной команды!'


class AvailabilityError(GenshinBotException):
    _msg = 'Вы не являетесь создателем или администратором чата!'


class ActionsAlreadyPublic(GenshinBotException):
    _msg = 'Манипуляции с пользовательскими командами уже являются общедоступными!'


class ActionsAlreadyRestricted(GenshinBotException):
    _msg = 'Манипуляции с пользовательскими командами уже являются ограниченными!'


class ActionError(GenshinBotException):
    _msg = 'В данном чате стоит ограничение на изменение пользовательских команд!'


class CommandNotSpecified(GenshinBotException):
    _msg = 'Вы не указали название команды!'


class CommandAlreadyExist(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"В данном чате уже существует команда '{name}'!"


class CommandNotExist(GenshinBotException):
    _msg = 'Невозможно удалить несуществующую команду!'


class CommandReserved(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"Название '{name}' зарезервировано одной из стандартных команд бота!"


class AdditionsNotSpecified(GenshinBotException):
    _msg = 'Укажите сообщение и/или прикрепите медиафайл для создания команды!'


class BotPrivilegesError(GenshinBotException):
    _msg = 'Для совершения данного действия боту нужны права администратора в чате!'
