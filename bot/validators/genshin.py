from bot.validators import BaseValidator
from bot.errors.genshin import *
from bot.src.types.genshin import Characters


__all__ = ('AscensionValidator',)


class AscensionValidator(BaseValidator):
    @staticmethod
    def check_character_specified(name: str) -> None:
        if not name:
            raise CharacterNotSpecified

    @staticmethod
    def check_character_available(name: str) -> None:
        if name in ('Итер', 'Люмин', 'Путешественник'):
            raise CharacterNotAvailable

    def check_character_exists(self, name: str) -> None:
        if name not in [character.value for character in Characters]:
            raise CharacterNotExists(self._message.text.lstrip('!ресы'))
