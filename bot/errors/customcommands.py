from bot.errors import GenshinBotException


__all__ = (
    'CommandsNotCreated',
    'AvailabilityError',
    'AlreadyPublic',
    'AlreadyRestricted',
    'ManipulationError',
    'CommandNotSpecified',
    'CommandAlreadyExists',
    'CommandNotExists',
    'CommandReserved',
    'AdditionNotSpecified'
)


class CommandsNotCreated(GenshinBotException):
    _msg = 'В данном чате не создано ни одной команды!'


class AvailabilityError(GenshinBotException):
    _msg = 'Вы не являетесь создателем или администратором чата!'


class AlreadyPublic(GenshinBotException):
    _msg = 'Манипуляции с пользовательскими командами уже являются общедоступными!'


class AlreadyRestricted(GenshinBotException):
    _msg = 'Манипуляции с пользовательскими командами уже являются ограниченными!'


class ManipulationError(GenshinBotException):
    _msg = 'В данном чате стоит ограничение на изменение пользовательских команд!'


class CommandNotSpecified(GenshinBotException):
    _msg = 'Вы не указали название команды!'


class CommandAlreadyExists(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"В данном чате уже существует команда '{name}'!"


class CommandNotExists(GenshinBotException):
    _msg = 'Невозможно удалить несуществующую команду!'


class CommandReserved(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"Название '{name}' зарезервировано одной из стандартных команд бота!"


class AdditionNotSpecified(GenshinBotException):
    _msg = 'Укажите сообщение и/или прикрепите медиафайл для создания команды!'
