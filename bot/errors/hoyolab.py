from bot.errors import GenshinBotException


__all__ = (
    'AccountAlreadyLinked',
    'NotEnoughCookies',
    'CookieSyntaxError',
    'InvalidAccountCookies',
    'AccountNotExists',
    'AccountNotFound',
    'ReplyMessageNotAttached',
    'RedeemCodeNotSpecified',
    'CommandNotAllowed'
)


class AccountAlreadyLinked(GenshinBotException):
    _msg = 'Ваши данные уже имеются в базе!'


class NotEnoughCookies(GenshinBotException):
    _msg = 'Вы указали не все необходимые для привязки данные!'


class CookieSyntaxError(GenshinBotException):
    _msg = 'При указании данных нарушен синтаксис!'


class InvalidAccountCookies(GenshinBotException):
    _msg = 'Указанные игровые данные не являются действительными!'


class AccountNotExists(GenshinBotException):
    _msg = 'Ваших данных нет в базе!'


class AccountNotFound(GenshinBotException):
    def __init__(self, for_other_user: bool) -> None:
        if for_other_user:
            self.__class__._msg = 'В базе отсутствуют данные указанного игрока!'
        else:
            self.__class__._msg = 'В базе отсутствуют ваши данные!'


class ReplyMessageNotAttached(GenshinBotException):
    def __init__(self, datatype: str) -> None:
        datatypes = {
            'Notes': 'просмотра его игровых заметок',
            'Stats': 'просмотра его игровой статистики',
            'Rewards': 'просмотра его игровых наград',
            'Redeem': 'активации ему промокодов',
            'Diary': 'просмотра его дневника путешественника'
        }
        self.__class__._msg = f"Не прикреплено сообщение другого игрока для {datatypes[datatype]}!"


class RedeemCodeNotSpecified(GenshinBotException):
    _msg = 'Не указан ни один промокод!'


class CommandNotAllowed(GenshinBotException):
    _msg = 'Вы не можете воспользоваться данной командой, т.к. не привязали свой игровой аккаунт!'


