class RandomPictureException(Exception):
    _msg: str = ''

    @property
    def error(self) -> str:
        return f"Ошибка: {self._msg}"


class QuantityNotSpecifiedError(RandomPictureException):
    _msg = 'Вы не указали  количество изображений для поиска!'


class QuantityOverflowError(RandomPictureException):
    _msg = 'Нельзя указать более 10 изображений за раз!'


class TagOverflowError(RandomPictureException):
    _msg = 'Нельзя указать более 3 тегов за раз!'
