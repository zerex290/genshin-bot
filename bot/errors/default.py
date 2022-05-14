from bot.errors import GenshinBotException


__all__ = (
    'ChoiceOptionsNotSpecified',
    'ReplyMessageError',
    'ReplyMessageTextError',
    'TimerNotSpecified',
    'TimerSyntaxError',
    'AttachmentError',
    'AttachmentTypeError',
    'PictureQuantityNotSpecified',
    'PictureQuantityOverflow',
    'TagQuantityOverflow'
)


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


class PictureQuantityNotSpecified(GenshinBotException):
    _msg = 'Вы не указали  количество изображений для поиска!'


class PictureQuantityOverflow(GenshinBotException):
    _msg = 'Нельзя указать более 10 изображений за раз!'


class TagQuantityOverflow(GenshinBotException):
    _msg = 'Нельзя указать более 3 тегов за раз!'
