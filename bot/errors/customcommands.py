class CommandCreationException(Exception):
    _msg: str = ''

    @property
    def error(self) -> str:
        return f"Ошибка: {self._msg}"


class AvailabilityError(CommandCreationException):
    _msg = 'В данном чате стоит ограничение на добавление команд!'


class EmptyNameError(CommandCreationException):
    _msg = 'Вы не указали название команды!'


class CommandExistsError(CommandCreationException):
    def __init__(self, name: str) -> None:
        self.name = name
        self.__class__._msg = f"В данном чате уже существует команда '{self.name}'!"


class CommandReservedError(CommandCreationException):
    def __init__(self, name: str) -> None:
        self.name = name
        self.__class__._msg = f"Название '{self.name}' зарезервировано одной из стандартных команд бота!"


class NotAnyAdditionError(CommandCreationException):
    _msg = 'Укажите сообщение или прикрепите медиафайл для создания команды!'
