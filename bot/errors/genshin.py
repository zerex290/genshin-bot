from bot.errors import GenshinBotException


__all__ = (
    'CharacterNotSpecified',
    'CharacterNotAvailable',
    'CharacterNotExists'
)


class CharacterNotSpecified(GenshinBotException):
    _msg = 'Вы не указали имя персонажа!'


class CharacterNotAvailable(GenshinBotException):
    _msg = 'Материалы возвышения данного персонажа можно посмотреть только в интерактивной базе данных!'


class CharacterNotExists(GenshinBotException):
    def __init__(self, name: str) -> None:
        self.__class__._msg = f"Не найден персонаж с именем {name}!"
