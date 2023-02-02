from . import GenshinBotException


__all__ = (
    'AccountAlreadyLinked',
    'NotEnoughCookies',
    'CookieSyntaxError',
    'InvalidAccountCookies',
    'AccountUnlinked',
    'AccountNotExist',
    'DisplayAlreadyLong',
    'DisplayAlreadyShort',
    'IncorrectDisplayType',
    'RedeemCodeNotSpecified',
    'CommandNotAllowed',
    'NotificationsAlreadyEnabled',
    'NotificationsAlreadyDisabled',
    'NotificationValueInvalid',
    'NotificationValueRangeInvalid',
    'SpiralAbyssLocked'
)


class AccountAlreadyLinked(GenshinBotException):
    _msg = 'Ваши данные уже имеются в базе!'


class NotEnoughCookies(GenshinBotException):
    _msg = 'Вы указали не все необходимые для привязки данные!'


class CookieSyntaxError(GenshinBotException):
    _msg = 'При указании данных нарушен синтаксис!'


class InvalidAccountCookies(GenshinBotException):
    _msg = 'Указанные игровые данные не являются действительными!'


class AccountUnlinked(GenshinBotException):
    _msg = 'Ваших данных нет в базе!'


class AccountNotExist(GenshinBotException):
    _ARTICLE = (
        'Статья с инструкцией по привязке игрового аккаунта: '
        'https://vk.com/@bot_genshin-genshin-register-guide'
    )

    def __init__(self, for_other_user: bool) -> None:
        if for_other_user:
            self.__class__._msg = f"Игровой аккаунт указанного игрока не привязан к базе!\n{self._ARTICLE}"
        else:
            self.__class__._msg = f"Ваш игровой аккаунт не привязан к базе!\n{self._ARTICLE}"


class DisplayAlreadyLong(GenshinBotException):
    _msg = 'Текстовое отображение для данной команды уже было включено!'


class DisplayAlreadyShort(GenshinBotException):
    _msg = 'Графическое отображение для данной команды уже было включено!'


class IncorrectDisplayType(GenshinBotException):
    def __init__(self, d_type: str) -> None:
        self.__class__._msg = f"Параметр '{d_type}' не распознан! Доступные параметры: 'текст', 'пик'."


class RedeemCodeNotSpecified(GenshinBotException):
    _msg = 'Не указан ни один промокод!'


class CommandNotAllowed(GenshinBotException):
    _msg = 'Вы не можете воспользоваться данной командой, т.к. не привязали свой игровой аккаунт!'


class NotificationsAlreadyEnabled(GenshinBotException):
    _msg = 'В данном чате уже включено автоматическое напоминание потратить смолу!'


class NotificationsAlreadyDisabled(GenshinBotException):
    _msg = 'В данном чате уже выключено автоматическое напоминание потратить смолу!'


class NotificationValueInvalid(GenshinBotException):
    _msg = 'Заданное минимальное значение смолы не является корректным!'


class NotificationValueRangeInvalid(GenshinBotException):
    _msg = 'Заданное минимальное значение смолы выходит за рамки допустимого диапазона!'


class SpiralAbyssLocked(GenshinBotException):
    _msg = 'Использование данной команды недоступно для игроков с прогрессом витой бездны меньше 9 этажа!'
