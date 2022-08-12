from . import GenshinBotException


__all__ = (
    'AutocorrectionAlreadyEnabled',
    'AutocorrectionAlreadyDisabled',
    'ChoiceOptionsNotSpecified',
    'ReplyMessageError',
    'ReplyMessageTextError',
    'TimerNotSpecified',
    'TimerSyntaxError',
    'AttachmentError',
    'AttachmentTypeError',
    'UserIsNotDon',
    'FavCountNotDefined',
    'FavCountRangeInvalid',
    'PictureQuantityNotSpecified',
    'PictureQuantityOverflow',
    'TagQuantityOverflow',
)


class AutocorrectionAlreadyEnabled(GenshinBotException):
    _msg = 'Автокоррекция команд уже включена!'


class AutocorrectionAlreadyDisabled(GenshinBotException):
    _msg = 'Автокоррекция команд уже выключена!'


class ChoiceOptionsNotSpecified(GenshinBotException):
    _msg = 'Не указаны варианты для выбора!'


class ReplyMessageError(GenshinBotException):
    _msg = 'Вы не прикрепили сообщение, текст которого нужно конвертировать!'


class ReplyMessageTextError(GenshinBotException):
    _msg = 'Сообщение, которое вы прикрепили, не содержит текста!'


class TimerNotSpecified(GenshinBotException):
    _msg = 'Не задано время для установки таймера!'


class TimerSyntaxError(GenshinBotException):
    _msg = 'При установке таймера был нарушен синтаксис!'


class AttachmentError(GenshinBotException):
    _msg = 'Не прикреплены изображения для пересылки!'


class AttachmentTypeError(GenshinBotException):
    _msg = 'Пересылать можно только изображения!'


class UserIsNotDon(GenshinBotException):
    _msg = 'Использование данной опции доступно только платным подписчикам группы!'


class FavCountNotDefined(GenshinBotException):
    _msg = 'Вы не указали минимальное количество лайков, которое должно быть у найденных ботом изображений!'


class FavCountRangeInvalid(GenshinBotException):
    _msg = 'Заданное кол-во лайков выходит за рамки допустимого диапазона!'


class PictureQuantityNotSpecified(GenshinBotException):
    _msg = 'Вы не указали  количество изображений для поиска!'


class PictureQuantityOverflow(GenshinBotException):
    _msg = 'Нельзя указать более 10 изображений за раз!'


class TagQuantityOverflow(GenshinBotException):
    def __init__(self, is_interactive: bool):
        if is_interactive:
            self.__class__._msg = 'В интерактивном режиме нельзя указать более 2 тегов за раз!'
        else:
            self.__class__._msg = 'Нельзя указать более 3 тегов за раз!'
